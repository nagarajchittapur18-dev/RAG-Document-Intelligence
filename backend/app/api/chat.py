import logging
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.schemas.chat import (
    AskQuestionRequest,
    AskQuestionResponse,
    ChatMessageItem,
    ChatSessionItem,
    ChatSessionListResponse,
    ChatSessionMessagesResponse,
    CreateSessionRequest,
    SourceCitation,
)
from app.services.document_store import DatabaseManager, UserRecord
from app.services.gemini import GeminiService
from app.services.retrieval import RetrievalService
from app.services.vector_store import VectorStore
from app.utils.dependencies import get_current_user

logger = logging.getLogger("ragmate.api.chat")
router = APIRouter(prefix="/chat", tags=["Chat & QA"])

# Shared service instances
vector_store = VectorStore()
retrieval_service = RetrievalService(vector_store=vector_store)
gemini_service = GeminiService()
db = DatabaseManager()


@router.post(
    "/ask",
    response_model=AskQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a document-grounded question",
    description="Embeds the user query, retrieves relevant chunks from ChromaDB (strictly scoped to the authenticated user), and generates an answer using Google Gemini with exact page citations.",
)
async def ask_question(
    request: AskQuestionRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    clean_query = request.question.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    t_start = time.perf_counter()
    k = request.top_k or settings.TOP_K

    # Validate document IDs if provided: ensure all documents exist and belong to current_user
    valid_doc_ids: Optional[List[str]] = None
    if request.document_ids:
        valid_doc_ids = []
        for doc_id in request.document_ids:
            doc = db.get_document(doc_id)
            if not doc or doc.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{doc_id}' not found.",
                )
            valid_doc_ids.append(doc_id)

    # Validate chat session if provided
    active_session_id = request.session_id
    if active_session_id:
        session = db.get_chat_session(active_session_id, current_user.id)
        if not session:
            # If session doesn't exist for user, raise 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session '{active_session_id}' not found.",
            )

    try:
        # Step 1: Retrieve context chunks using existing RetrievalService with user_id scoping!
        contexts = retrieval_service.retrieve(
            query=clean_query,
            top_k=k,
            document_ids=valid_doc_ids,
            user_id=current_user.id,
        )

        # Step 2: Synthesize grounded answer using existing GeminiService
        rag_response = gemini_service.generate_grounded_answer(
            question=clean_query,
            contexts=contexts,
        )

        total_latency_ms = (time.perf_counter() - t_start) * 1000

        # Step 3: Format sources preserving provenance
        citation_sources = [
            SourceCitation(
                document_id=s.document_id,
                document_name=s.document_name,
                page_number=s.page_number,
                chunk_id=s.chunk_id,
                similarity_score=s.similarity_score,
                snippet=s.snippet,
            )
            for s in rag_response.sources
        ]

        # Step 4: Persist messages in chat session if active
        if active_session_id:
            # Save user prompt
            db.add_message(
                session_id=active_session_id,
                role="user",
                content=clean_query,
            )
            # Save assistant response with sources
            db.add_message(
                session_id=active_session_id,
                role="assistant",
                content=rag_response.answer,
                sources=[s.model_dump() for s in citation_sources],
            )

        logger.info(
            "QA query executed for %s: '%s' (retrieved: %d chunks, latency: %.1f ms, grounded: %s)",
            current_user.email,
            clean_query,
            len(contexts),
            total_latency_ms,
            rag_response.is_grounded,
        )

        return AskQuestionResponse(
            answer=rag_response.answer,
            sources=citation_sources,
            retrieved_chunks=len(contexts),
            response_time_ms=round(total_latency_ms, 2),
            session_id=active_session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing question '%s': %s", clean_query, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the answer. Please try again.",
        )


# =============================================================================
# CHAT SESSION MANAGEMENT ENDPOINTS
# =============================================================================

@router.post(
    "/sessions",
    response_model=ChatSessionItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
)
async def create_chat_session(
    request: CreateSessionRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    session = db.create_chat_session(
        user_id=current_user.id,
        title=request.title or "New Conversation",
    )
    return ChatSessionItem(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
    summary="List all chat sessions for the current user",
)
async def list_chat_sessions(current_user: UserRecord = Depends(get_current_user)):
    sessions = db.list_chat_sessions_for_user(current_user.id)
    items = [
        ChatSessionItem(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]
    return ChatSessionListResponse(sessions=items)


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionMessagesResponse,
    summary="Get conversation history for a specific chat session",
)
async def get_chat_session(
    session_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    session = db.get_chat_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    raw_messages = db.get_messages_for_session(session_id)
    messages = [
        ChatMessageItem(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            sources=m.sources,
            created_at=m.created_at,
        )
        for m in raw_messages
    ]

    return ChatSessionMessagesResponse(
        session=ChatSessionItem(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
        ),
        messages=messages,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a chat session and its history",
)
async def delete_chat_session(
    session_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    deleted = db.delete_chat_session(session_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )
    return {"message": "Chat session deleted successfully"}
