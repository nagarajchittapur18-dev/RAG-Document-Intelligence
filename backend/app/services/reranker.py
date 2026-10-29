import logging
import math
import time
from typing import List, Optional
import torch
from sentence_transformers import CrossEncoder

from app.config import settings
from app.services.vector_store import SearchResult

logger = logging.getLogger("ragmate.reranker")


class RerankerService:
    """
    Two-stage retrieval reranking engine using HuggingFace CrossEncoders.
    Evaluates (query, document_chunk) pairs jointly to provide deep contextual relevance
    scoring, ensuring high precision while preserving original vector retrieval provenance.
    """

    _instance: Optional["RerankerService"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        model_name: Optional[str] = None,
        enabled: Optional[bool] = None,
        device: Optional[str] = None,
    ):
        if getattr(self, "_initialized", False):
            return

        self.model_name = model_name or settings.RERANKER_MODEL
        self.enabled = (
            enabled
            if enabled is not None
            else getattr(settings, "RERANKING_ENABLED", getattr(settings, "RERANKER_ENABLED", True))
        )
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_text_len = getattr(settings, "MAX_RERANK_TEXT_LENGTH", 1000)
        self._model: Optional[CrossEncoder] = None
        self._load_error: Optional[str] = None
        self._initialized = True

        logger.info(
            "RerankerService initialized (enabled=%s, model=%s, device=%s)",
            self.enabled,
            self.model_name,
            self.device,
        )

    def _get_model(self) -> Optional[CrossEncoder]:
        """Lazy-loads the CrossEncoder model on demand."""
        if not self.enabled:
            return None

        if self._model is not None:
            return self._model

        if self._load_error is not None:
            return None

        try:
            logger.info("Loading CrossEncoder model '%s' on %s...", self.model_name, self.device)
            t0 = time.perf_counter()
            try:
                self._model = CrossEncoder(self.model_name, device=self.device, local_files_only=True)
            except Exception:
                self._model = CrossEncoder(self.model_name, device=self.device)
            logger.info("CrossEncoder '%s' successfully loaded in %.2f ms", self.model_name, (time.perf_counter() - t0) * 1000)
            return self._model
        except Exception as e:
            logger.warning(
                "Failed to initialize CrossEncoder model '%s': %s. Reranking will fall back to vector retrieval.",
                self.model_name,
                str(e),
            )
            self._load_error = str(e)
            return None

    def rerank(
        self,
        query: str,
        candidates: List[SearchResult],
        top_k: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Reranks a candidate list of SearchResult chunks using cross-encoder scoring.
        Applies sigmoid normalization to raw logits to yield calibrated 0.00-1.00 relevance scores.
        Preserves original similarity_score as retrieval_score.
        Falls back smoothly to vector similarity ordering if disabled or on any error.
        """
        if not candidates:
            return []

        clean_query = query.strip()
        target_k = top_k if top_k is not None else len(candidates)

        # Fallback path if reranker is disabled or only 1 candidate exists
        if not self.enabled or len(candidates) <= 1:
            sorted_candidates = sorted(candidates, key=lambda x: x.similarity_score, reverse=True)
            for c in sorted_candidates:
                if c.rerank_score is None:
                    c.rerank_score = c.similarity_score
                c.metadata["retrieval_score"] = c.similarity_score
                c.metadata["rerank_score"] = c.rerank_score
            return sorted_candidates[:target_k]

        model = self._get_model()
        if model is None:
            logger.warning("Reranker model unavailable. Falling back to vector similarity ranking.")
            sorted_candidates = sorted(candidates, key=lambda x: x.similarity_score, reverse=True)
            for c in sorted_candidates:
                if c.rerank_score is None:
                    c.rerank_score = c.similarity_score
                c.metadata["retrieval_score"] = c.similarity_score
                c.metadata["rerank_score"] = c.rerank_score
            return sorted_candidates[:target_k]

        t0 = time.perf_counter()
        try:
            # Construct (query, candidate_text) pairs with safe length truncation for scoring only
            pairs = [
                (clean_query, c.text[:self.max_text_len].strip())
                for c in candidates
            ]

            # Cross-encoder inference produces logits
            raw_scores = model.predict(pairs)

            reranked_results: List[SearchResult] = []
            for idx, c in enumerate(candidates):
                raw_logit = float(raw_scores[idx])

                # Sigmoid normalization maps logit into [0.0, 1.0] probability scale
                # 1 / (1 + exp(-z))
                try:
                    norm_score = 1.0 / (1.0 + math.exp(-raw_logit))
                except OverflowError:
                    norm_score = 1.0 if raw_logit > 0 else 0.0

                rerank_score = round(float(norm_score), 4)

                # Clone or update SearchResult with both scores preserved
                c.rerank_score = rerank_score
                c.metadata["retrieval_score"] = c.similarity_score
                c.metadata["rerank_score"] = rerank_score
                reranked_results.append(c)

            # Sort descending by rerank_score, using similarity_score as tie-breaker
            reranked_results.sort(
                key=lambda x: (x.rerank_score if x.rerank_score is not None else 0.0, x.similarity_score),
                reverse=True,
            )

            latency_ms = (time.perf_counter() - t0) * 1000
            final_selection = reranked_results[:target_k]
            logger.info(
                "Reranking completed in %.2f ms: evaluated %d candidates, selected top %d",
                latency_ms,
                len(candidates),
                len(final_selection),
            )
            return final_selection

        except Exception as e:
            logger.error("Exception during cross-encoder reranking: %s. Using vector retrieval fallback.", str(e), exc_info=True)
            sorted_candidates = sorted(candidates, key=lambda x: x.similarity_score, reverse=True)
            for c in sorted_candidates:
                if c.rerank_score is None:
                    c.rerank_score = c.similarity_score
                c.metadata["retrieval_score"] = c.similarity_score
                c.metadata["rerank_score"] = c.rerank_score
            return sorted_candidates[:target_k]
