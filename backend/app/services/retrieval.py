import logging
import re
import time
from typing import Dict, List, Optional, Set, Tuple, Union
from app.config import settings
from app.services.reranker import RerankerService
from app.services.vector_store import SearchResult, VectorStore

logger = logging.getLogger("ragmate.retrieval")

COMPARISON_KEYWORDS = {
    "compare", "comparison", "difference", "differences",
    "similarity", "similarities", "versus", "vs", "vs.",
    "better", "contrast", "contrasting", "both", "differ",
    "between", "distinguish", "distinction",
}


def is_comparison_query(query: str) -> bool:
    """
    Deterministic, lightweight comparison query detection without LLM overhead.
    """
    tokens = set(re.findall(r'\b\w+\b', query.lower()))
    return bool(tokens & COMPARISON_KEYWORDS)


class RetrievalService:
    """
    Two-stage retrieval service coordinating candidate vector search, cross-encoder reranking,
    multi-tenant scoping, multi-document comparison balancing, and character budget enforcement.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        reranker: Optional[RerankerService] = None,
    ):
        self.vector_store = vector_store or VectorStore()
        self.reranker = reranker or RerankerService()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        document_ids: Optional[List[Union[str, int]]] = None,
        user_id: Optional[Union[str, int]] = None,
        min_similarity: Optional[float] = None,
        initial_top_k: Optional[int] = None,
        max_context_chars: Optional[int] = None,
        enable_reranking: Optional[bool] = None,
    ) -> List[SearchResult]:
        """
        Retrieves contextually relevant document chunks for a given query using two-stage retrieval:
        1. High-recall candidate search in ChromaDB (scoped strictly to user_id and document_ids).
        2. High-precision cross-encoder reranking to reorder candidates based on joint context scoring.
        """
        target_final_k = top_k if top_k is not None else settings.FINAL_TOP_K
        threshold = min_similarity if min_similarity is not None else settings.SIMILARITY_THRESHOLD
        char_limit = max_context_chars if max_context_chars is not None else settings.MAX_CONTEXT_CHARS

        clean_query = query.strip()
        if not clean_query:
            logger.warning("Empty query submitted to RetrievalService.")
            return []

        # Check if reranking is enabled
        use_reranker = (
            enable_reranking
            if enable_reranking is not None
            else (
                self.reranker.enabled
                and getattr(settings, "RERANKING_ENABLED", getattr(settings, "RERANKER_ENABLED", True))
            )
        )

        # Determine candidate fetch size: if reranking is active or multi-document, fetch candidate pool
        is_multi_doc = document_ids is None or len(document_ids) != 1
        default_candidates = (
            getattr(settings, "RERANKING_CANDIDATES", 15)
            if use_reranker
            else (settings.INITIAL_TOP_K if is_multi_doc else target_final_k)
        )
        candidate_k = initial_top_k or default_candidates
        candidate_k = max(candidate_k, target_final_k)

        logger.info(
            "Executing retrieval for query: '%s' (candidate_k=%d, final_k=%d, doc_ids=%s, user_id=%s, min_similarity=%.2f, reranker=%s)",
            clean_query,
            candidate_k,
            target_final_k,
            document_ids,
            user_id,
            threshold,
            use_reranker,
        )

        t0 = time.perf_counter()
        raw_candidates = self.vector_store.similarity_search(
            query_text=clean_query,
            top_k=candidate_k,
            document_ids=document_ids,
            user_id=user_id,
            min_similarity=threshold,
        )

        # 1. Deduplicate candidates by (document_id, chunk_id)
        seen: Set[Tuple[str, str]] = set()
        unique_candidates: List[SearchResult] = []
        for c in raw_candidates:
            key = (str(c.document_id), str(c.chunk_id))
            if key not in seen:
                seen.add(key)
                unique_candidates.append(c)

        if not unique_candidates:
            return []

        # 2. Stage 2: Cross-Encoder Reranking
        is_comparison = is_comparison_query(clean_query) and is_multi_doc
        if use_reranker:
            reranked_pool = self.reranker.rerank(
                query=clean_query,
                candidates=unique_candidates,
                top_k=None,  # Return all scored candidates so balancing can inspect them
            )

            # If comparison query across multiple documents, apply document-aware balancing
            if is_comparison and settings.ENABLE_DOCUMENT_BALANCING:
                final_results = self._balance_by_score(
                    candidates=reranked_pool,
                    final_top_k=target_final_k,
                    score_key=lambda x: x.rerank_score if x.rerank_score is not None else x.similarity_score,
                )
            else:
                final_results = reranked_pool[:target_final_k]
        else:
            # Vector-only retrieval
            if is_multi_doc and settings.ENABLE_DOCUMENT_BALANCING:
                final_results = self._balance_by_score(
                    candidates=unique_candidates,
                    final_top_k=target_final_k,
                    score_key=lambda x: x.similarity_score,
                )
            else:
                final_results = sorted(unique_candidates, key=lambda x: x.similarity_score, reverse=True)[:target_final_k]

        # 3. Enforce context character budget
        budgeted_results = self._enforce_character_budget(final_results, char_limit)

        latency_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "Retrieval pipeline complete in %.2f ms (reranker=%s): candidates=%d, selected=%d (from %d docs)",
            latency_ms,
            use_reranker,
            len(raw_candidates),
            len(budgeted_results),
            len({r.document_id for r in budgeted_results}),
        )
        return budgeted_results

    def _balance_by_score(
        self,
        candidates: List[SearchResult],
        final_top_k: int,
        score_key,
    ) -> List[SearchResult]:
        """
        Balances multi-document candidate representation in round-robin fashion,
        guaranteeing each represented document contributes its highest-scoring chunks.
        """
        distinct_docs = {c.document_id for c in candidates}
        if len(distinct_docs) <= 1:
            return sorted(candidates, key=score_key, reverse=True)[:final_top_k]

        doc_groups: Dict[str, List[SearchResult]] = {}
        for c in candidates:
            doc_groups.setdefault(c.document_id, []).append(c)

        for doc_id in doc_groups:
            doc_groups[doc_id].sort(key=score_key, reverse=True)

        sorted_doc_ids = sorted(
            doc_groups.keys(),
            key=lambda d: score_key(doc_groups[d][0]) if doc_groups[d] else 0.0,
            reverse=True,
        )

        balanced_selection: List[SearchResult] = []
        while len(balanced_selection) < final_top_k:
            added_in_round = False
            for doc_id in sorted_doc_ids:
                if doc_groups[doc_id]:
                    balanced_selection.append(doc_groups[doc_id].pop(0))
                    added_in_round = True
                    if len(balanced_selection) >= final_top_k:
                        break
            if not added_in_round:
                break

        return balanced_selection

    def _balance_and_deduplicate(
        self,
        candidates: List[SearchResult],
        final_top_k: int,
        max_context_chars: int,
        balance_documents: bool,
    ) -> List[SearchResult]:
        """
        Deduplicates chunks and balances representation across multiple documents
        for comparative questions.
        """
        # 1. Deduplicate by (document_id, chunk_id)
        seen: Set[Tuple[str, str]] = set()
        unique_candidates: List[SearchResult] = []
        for c in candidates:
            key = (str(c.document_id), str(c.chunk_id))
            if key not in seen:
                seen.add(key)
                unique_candidates.append(c)

        if not unique_candidates:
            return []

        distinct_docs = {c.document_id for c in unique_candidates}

        # 2. Single document or no balancing required
        if not balance_documents or len(distinct_docs) <= 1:
            sorted_chunks = sorted(unique_candidates, key=lambda x: x.similarity_score, reverse=True)[:final_top_k]
            return self._enforce_character_budget(sorted_chunks, max_context_chars)

        # 3. Multi-document balancing: group by document_id
        doc_groups: Dict[str, List[SearchResult]] = {}
        for c in unique_candidates:
            doc_groups.setdefault(c.document_id, []).append(c)

        for doc_id in doc_groups:
            doc_groups[doc_id].sort(key=lambda x: x.similarity_score, reverse=True)

        # Order documents by their highest similarity chunk
        sorted_doc_ids = sorted(
            doc_groups.keys(),
            key=lambda d: doc_groups[d][0].similarity_score if doc_groups[d] else 0.0,
            reverse=True,
        )

        balanced_selection: List[SearchResult] = []
        while len(balanced_selection) < final_top_k:
            added_in_round = False
            for doc_id in sorted_doc_ids:
                if doc_groups[doc_id]:
                    balanced_selection.append(doc_groups[doc_id].pop(0))
                    added_in_round = True
                    if len(balanced_selection) >= final_top_k:
                        break
            if not added_in_round:
                break

        return self._enforce_character_budget(balanced_selection, max_context_chars)

    def _enforce_character_budget(
        self,
        chunks: List[SearchResult],
        max_chars: int,
    ) -> List[SearchResult]:
        """Enforces a strict upper bound on total retrieved context character count."""
        budget_chunks: List[SearchResult] = []
        accumulated_chars = 0

        for chunk in chunks:
            chunk_len = len(chunk.text)
            if accumulated_chars + chunk_len > max_chars and budget_chunks:
                logger.warning(
                    "Context character budget reached (%d chars). Skipping remaining %d chunk(s).",
                    accumulated_chars,
                    len(chunks) - len(budget_chunks),
                )
                break
            budget_chunks.append(chunk)
            accumulated_chars += chunk_len

        return budget_chunks
