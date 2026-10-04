from typing import Any, Dict, List, Optional
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


# --- Phase 12 Academic Evaluation Schemas ---

class EvaluationQuestionSchema(BaseModel):
    id: str
    question: str
    document_id: str
    document_name: str
    expected_pages: List[int] = Field(default_factory=list)
    expected_chunk_ids: List[str] = Field(default_factory=list)
    reference_answer: str
    question_type: str
    difficulty: str
    selected_document_ids: Optional[List[str]] = Field(default_factory=list)


class EvaluationDatasetSummaryResponse(BaseModel):
    total_questions: int
    by_type: Dict[str, int]
    by_difficulty: Dict[str, int]
    by_document: Dict[str, int]
    unanswerable_count: int
    answerable_count: int
    dataset_version: str


class IRMetricsAtK(BaseModel):
    precision: float
    recall: float
    hit_rate: float
    page_hit_rate: float
    doc_hit_rate: float


class MethodBenchmarkResult(BaseModel):
    method_name: str
    reranking_enabled: bool
    metrics_by_k: Dict[str, IRMetricsAtK]
    mrr: float
    abstention_accuracy: float
    avg_retrieval_latency_ms: float
    avg_rerank_latency_ms: float
    avg_total_latency_ms: float


class RelativeImprovement(BaseModel):
    metric: str
    baseline: float
    reranked: float
    improvement_percentage: float


class BenchmarkRunRequest(BaseModel):
    dataset_path: Optional[str] = Field(None, description="Optional path to custom dataset JSON")
    candidate_k: Optional[int] = Field(15, ge=1, le=50, description="Candidate pool size N")
    k_values: Optional[List[int]] = Field([1, 3, 5, 10], description="List of K cutoffs to evaluate")
    include_generation: Optional[bool] = Field(False, description="Whether to invoke LLM generation during evaluation")
    limit: Optional[int] = Field(None, ge=1, description="Optional subset limit for fast evaluation")


class BenchmarkRunResponse(BaseModel):
    experiment_id: str
    timestamp: str
    dataset_version: str
    questions_evaluated: int
    baseline_vector: MethodBenchmarkResult
    enhanced_reranked: MethodBenchmarkResult
    improvements: List[RelativeImprovement]
    error_summary: Dict[str, int]
    summary_path: str


class ExperimentListItem(BaseModel):
    experiment_id: str
    timestamp: str
    dataset_version: str
    questions_evaluated: int
    vector_mrr: float
    reranked_mrr: float
    mrr_improvement_pct: float
    vector_hit5: float
    reranked_hit5: float
    hit5_improvement_pct: float
    avg_latency_ms: float
