import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Union
from app.config import settings
from app.services.vector_store import SearchResult, VectorStore

logger = logging.getLogger("ragmate.retrieval")


class RetrievalService:
    """
    Core retrieval service coordinating vector similarity search, multi-tenant scoping,
    multi-document balancing, deduplication, and threshold validation.
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        document_ids: Optional[List[Union[str, int]]] = None,
        user_id: Optional[Union[str, int]] = None,
        min_similarity: Optional[float] = None,
        initial_top_k: Optional[int] = None,
        max_context_chars: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Retrieves contextually relevant document chunks for a given query.
        Supports multi-document queries with document balancing and context size limits.
        """
        target_final_k = top_k if top_k is not None else settings.FINAL_TOP_K
        threshold = min_similarity if min_similarity is not None else settings.SIMILARITY_THRESHOLD
        char_limit = max_context_chars if max_context_chars is not None else settings.MAX_CONTEXT_CHARS

        clean_query = query.strip()
        if not clean_query:
            logger.warning("Empty query submitted to RetrievalService.")
            return []

        # Determine candidate fetch size: if multi-document or global search, fetch candidate pool
        is_multi_doc = document_ids is None or len(document_ids) != 1
        candidate_k = initial_top_k or (settings.INITIAL_TOP_K if is_multi_doc else target_final_k)
        candidate_k = max(candidate_k, target_final_k)

        logger.info(
            "Executing retrieval for query: '%s' (candidate_k=%d, final_k=%d, doc_ids=%s, user_id=%s, min_similarity=%.2f)",
            clean_query,
            candidate_k,
            target_final_k,
            document_ids,
            user_id,
            threshold,
        )

        t0 = time.perf_counter()
        raw_candidates = self.vector_store.similarity_search(
            query_text=clean_query,
            top_k=candidate_k,
            document_ids=document_ids,
            user_id=user_id,
            min_similarity=threshold,
        )

        # Apply multi-document balancing and deduplication
        final_results = self._balance_and_deduplicate(
            candidates=raw_candidates,
            final_top_k=target_final_k,
            max_context_chars=char_limit,
            balance_documents=settings.ENABLE_DOCUMENT_BALANCING and is_multi_doc,
        )

        latency_ms = (time.perf_counter() - t0) * 1000

        logger.info(
            "Retrieval complete in %.2f ms: candidates=%d, final_selected=%d (from %d docs)",
            latency_ms,
            len(raw_candidates),
            len(final_results),
            len({r.document_id for r in final_results}),
        )
        return final_results

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
