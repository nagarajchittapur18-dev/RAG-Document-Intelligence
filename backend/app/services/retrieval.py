import logging
import time
from typing import List, Optional, Union
from app.config import settings
from app.services.vector_store import SearchResult, VectorStore

logger = logging.getLogger("ragmate.retrieval")


class RetrievalService:
    """
    Core retrieval service coordinating vector similarity search, multi-tenant scoping,
    and threshold validation.
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
    ) -> List[SearchResult]:
        """
        Retrieves top-k contextually relevant document chunks for a given query.
        Filters by user_id and document_ids when provided.
        """
        k = top_k if top_k is not None else settings.TOP_K
        threshold = min_similarity if min_similarity is not None else settings.SIMILARITY_THRESHOLD

        clean_query = query.strip()
        if not clean_query:
            logger.warning("Empty query submitted to RetrievalService.")
            return []

        logger.info(
            "Executing retrieval for query: '%s' (top_k=%d, doc_ids=%s, user_id=%s, min_similarity=%.2f)",
            clean_query,
            k,
            document_ids,
            user_id,
            threshold,
        )

        t0 = time.perf_counter()
        results = self.vector_store.similarity_search(
            query_text=clean_query,
            top_k=k,
            document_ids=document_ids,
            user_id=user_id,
            min_similarity=threshold,
        )
        latency_ms = (time.perf_counter() - t0) * 1000

        logger.info(
            "Retrieval complete in %.2f ms: found %d relevant chunks above threshold %.2f",
            latency_ms,
            len(results),
            threshold,
        )
        return results
