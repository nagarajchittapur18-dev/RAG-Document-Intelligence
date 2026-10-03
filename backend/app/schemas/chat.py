from typing import List, Optional
from pydantic import BaseModel, Field


class AskQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language question to ask")
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of document IDs to scope retrieval to. If omitted or empty, queries all documents.",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of context chunks to retrieve (default from settings: 5)",
    )


class SourceCitation(BaseModel):
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Original filename")
    page_number: int = Field(..., description="1-indexed source page")
    chunk_id: str = Field(..., description="Deterministic chunk ID")
    similarity_score: Optional[float] = Field(None, description="Cosine similarity score")
    snippet: Optional[str] = Field(None, description="Excerpt preview")


class AskQuestionResponse(BaseModel):
    answer: str = Field(..., description="Grounded answer synthesized by Gemini or safe fallback")
    sources: List[SourceCitation] = Field(default_factory=list, description="Preserved provenance citations")
    retrieved_chunks: int = Field(0, description="Count of retrieved context chunks")
    response_time_ms: float = Field(0.0, description="Total pipeline latency in milliseconds")
