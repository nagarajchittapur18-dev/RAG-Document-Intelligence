import logging
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.evaluation import (
    EvaluationChunkItem,
    RetrievalCompareRequest,
    RetrievalCompareResponse,
)
from app.services.document_store import DatabaseManager, UserRecord
from app.services.reranker import RerankerService
from app.services.vector_store import VectorStore
from app.utils.dependencies import get_current_user

logger = logging.getLogger("ragmate.api.evaluation")
router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarking"])

vector_store = VectorStore()
reranker_service = RerankerService()
db = DatabaseManager()


@router.post(
    "/retrieval-compare",
    response_model=RetrievalCompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Vector-Only retrieval vs Vector + Cross-Encoder Reranking",
    description="Academic research endpoint evaluating the impact of two-stage retrieval. Returns both vector-ranked and cross-encoder reranked candidate lists with individual latency benchmarks.",
)
async def compare_retrieval_methods(
    request: RetrievalCompareRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    clean_query = request.question.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    # Validate document IDs ownership
    valid_doc_ids: Optional[List[str]] = None
    if request.document_ids:
        valid_doc_ids = []
        for doc_id in request.document_ids:
            doc = db.get_document(doc_id)
            if not doc or doc.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{doc_id}' not found or unauthorized.",
                )
            valid_doc_ids.append(doc_id)

    num_docs = len(valid_doc_ids) if valid_doc_ids else len(db.list_documents_for_user(current_user.id))
    candidate_k = request.candidate_k or 15
    final_k = request.final_k or 5

    # 1. Measure Vector Retrieval Latency
    t_v0 = time.perf_counter()
    candidates = vector_store.similarity_search(
        query_text=clean_query,
        top_k=candidate_k,
        document_ids=valid_doc_ids,
        user_id=current_user.id,
    )
    vector_latency_ms = (time.perf_counter() - t_v0) * 1000

    # Deduplicate candidates
    seen = set()
    unique_candidates = []
    for c in candidates:
        key = (str(c.document_id), str(c.chunk_id))
        if key not in seen:
            seen.add(key)
            unique_candidates.append(c)

    # Method A: Vector-Only Top-K
    vector_only_sorted = sorted(unique_candidates, key=lambda x: x.similarity_score, reverse=True)[:final_k]
    vector_items = [
        EvaluationChunkItem(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            document_name=c.document_name,
            page_number=c.page_number,
            text=c.text,
            similarity_score=round(c.similarity_score, 4),
            rerank_score=None,
            rank=idx + 1,
        )
        for idx, c in enumerate(vector_only_sorted)
    ]

    # Method B: Vector + Cross-Encoder Reranking
    t_r0 = time.perf_counter()
    reranked_pool = reranker_service.rerank(
        query=clean_query,
        candidates=[c.model_copy() for c in unique_candidates],
        top_k=final_k,
    )
    rerank_latency_ms = (time.perf_counter() - t_r0) * 1000

    reranked_items = [
        EvaluationChunkItem(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            document_name=c.document_name,
            page_number=c.page_number,
            text=c.text,
            similarity_score=round(c.similarity_score, 4),
            rerank_score=round(c.rerank_score, 4) if c.rerank_score is not None else None,
            rank=idx + 1,
        )
        for idx, c in enumerate(reranked_pool)
    ]

    total_latency_ms = vector_latency_ms + rerank_latency_ms

    return RetrievalCompareResponse(
        question=clean_query,
        documents_searched=num_docs,
        candidate_count=len(unique_candidates),
        vector_only_chunks=vector_items,
        reranked_chunks=reranked_items,
        vector_latency_ms=round(vector_latency_ms, 2),
        rerank_latency_ms=round(rerank_latency_ms, 2),
        total_latency_ms=round(total_latency_ms, 2),
    )
