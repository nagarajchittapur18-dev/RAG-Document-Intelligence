from typing import List, Optional
from pydantic import BaseModel, Field


class RetrievalCompareRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Evaluation question to benchmark")
    document_ids: Optional[List[str]] = Field(None, description="Optional document IDs scope")
    candidate_k: Optional[int] = Field(15, ge=1, le=50, description="Candidate pool size retrieved from vector store")
    final_k: Optional[int] = Field(5, ge=1, le=20, description="Final top-k chunks selected")


class EvaluationChunkItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    text: str
    similarity_score: float
    rerank_score: Optional[float] = None
    rank: int


class RetrievalCompareResponse(BaseModel):
    question: str
    documents_searched: int
    candidate_count: int
    vector_only_chunks: List[EvaluationChunkItem]
    reranked_chunks: List[EvaluationChunkItem]
    vector_latency_ms: float
    rerank_latency_ms: float
    total_latency_ms: float
