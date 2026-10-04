from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AskQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=3000, description="Natural language question to ask (max 3000 chars)")
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of document IDs to scope retrieval to. If omitted or empty, queries all documents.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional chat session ID to associate question and answer with",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of context chunks to retrieve (default from settings: 5)",
    )


class SessionMessageRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=3000, description="Question to submit to the active chat session (max 3000 chars)")
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Optional top_k chunks override",
    )


class RenameSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Updated conversation title")


class SourceCitation(BaseModel):
    citation_id: int = Field(..., description="1-indexed sequential citation identifier [1], [2], ...")
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Original filename")
    page_number: int = Field(..., description="1-indexed source page")
    chunk_id: str = Field(..., description="Deterministic chunk ID")
    similarity_score: Optional[float] = Field(None, description="Cosine similarity score")
    relevance_score: Optional[float] = Field(None, description="Normalized relevance score (0.00 - 1.00)")
    retrieval_score: Optional[float] = Field(None, description="Initial vector similarity score (0.00 - 1.00)")
    rerank_score: Optional[float] = Field(None, description="Cross-encoder reranking relevance score (0.00 - 1.00)")
    snippet: Optional[str] = Field(None, description="Excerpt preview (300-500 chars)")


class AskQuestionResponse(BaseModel):
    answer: str = Field(..., description="Grounded answer synthesized by Gemini or safe fallback")
    sources: List[SourceCitation] = Field(default_factory=list, description="Preserved provenance citations")
    retrieved_chunks: int = Field(0, description="Count of retrieved context chunks")
    documents_searched: int = Field(0, description="Count of distinct documents searched")
    response_time_ms: float = Field(0.0, description="Total pipeline latency in milliseconds")
    session_id: Optional[str] = Field(None, description="Chat session ID if conversation is tracked")
    retrieval_debug: Optional[Dict[str, Any]] = Field(None, description="Optional diagnostic metrics for retrieval and reranking")


class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field("New Conversation", max_length=150, description="Title for the chat session")
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of document IDs to bind to this session",
    )


class ChatSessionItem(BaseModel):
    id: str
    title: str
    document_ids: List[str] = Field(default_factory=list)
    document_count: int = 0
    message_count: int = 0
    created_at: str
    updated_at: str


class ChatSessionListResponse(BaseModel):
    sessions: List[ChatSessionItem]


class SessionDocumentInfo(BaseModel):
    id: str
    name: str
    pages: int = 0
    status: str = "completed"


class ChatMessageItem(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: List[dict] = Field(default_factory=list)
    created_at: str


class ChatSessionMessagesResponse(BaseModel):
    session: ChatSessionItem
    documents: List[SessionDocumentInfo] = Field(default_factory=list)
    unavailable_documents_count: int = 0
    warning_message: Optional[str] = None
    messages: List[ChatMessageItem]
