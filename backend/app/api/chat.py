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
    description="Embeds the user query, retrieves relevant chunks from ChromaDB (strictly scoped to the authenticated user and selected documents), and generates an answer using Google Gemini with exact page citations.",
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
    k = request.top_k or settings.FINAL_TOP_K

    active_session_id = request.session_id
    if active_session_id:
        session = db.get_chat_session(active_session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session '{active_session_id}' not found.",
            )

    # 1. Determine and validate document scope
    valid_doc_ids: Optional[List[str]] = None
    if request.document_ids is not None and len(request.document_ids) > 0:
        # User explicitly supplied document IDs
        valid_doc_ids = []
        for doc_id in request.document_ids:
            doc = db.get_document(doc_id)
            if not doc or doc.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{doc_id}' not found or unauthorized.",
                )
            valid_doc_ids.append(doc_id)

        # If a session is active, bind this document scope to it
        if active_session_id:
            db.bind_session_documents(active_session_id, valid_doc_ids)

    elif active_session_id:
        # Check if the active session has previously bound documents
        bound_doc_ids = db.get_session_documents(active_session_id)
        if bound_doc_ids:
            valid_doc_ids = []
            for doc_id in bound_doc_ids:
                doc = db.get_document(doc_id)
                if doc and doc.user_id == current_user.id:
                    valid_doc_ids.append(doc_id)

    # Compute documents_searched count
    if valid_doc_ids:
        documents_searched = len(valid_doc_ids)
    else:
        # Mode 3: Search all user documents
        all_user_docs = db.list_documents_for_user(current_user.id)
        documents_searched = len(all_user_docs)

    try:
        # Step 2: Retrieve context chunks using multi-document balanced RetrievalService
        contexts = retrieval_service.retrieve(
            query=clean_query,
            top_k=k,
            document_ids=valid_doc_ids,
            user_id=current_user.id,
        )
        # Step 3: Fetch recent conversation history if active session
        conversation_history = None
        if active_session_id:
            raw_hist = db.get_messages_for_session(active_session_id)
            conversation_history = [{"role": m.role, "content": m.content} for m in raw_hist[-4:]]

        # Step 4: Synthesize grounded answer using GeminiService
        rag_response = gemini_service.generate_grounded_answer(
            question=clean_query,
            contexts=contexts,
            conversation_history=conversation_history,
        )

        total_latency_ms = (time.perf_counter() - t_start) * 1000

        # Step 5: Format deduplicated source citations
        seen_citations = set()
        citation_sources: List[SourceCitation] = []
        for s in rag_response.sources:
            cit_key = (s.document_id, s.chunk_id)
            if cit_key not in seen_citations:
                seen_citations.add(cit_key)
                citation_sources.append(
                    SourceCitation(
                        document_id=s.document_id,
                        document_name=s.document_name,
                        page_number=s.page_number,
                        chunk_id=s.chunk_id,
                        similarity_score=s.similarity_score,
                        snippet=s.snippet,
                    )
                )

        # Step 6: Persist messages in chat session if active
        if active_session_id:
            db.add_message(
                session_id=active_session_id,
                role="user",
                content=clean_query,
            )
            db.add_message(
                session_id=active_session_id,
                role="assistant",
                content=rag_response.answer,
                sources=[s.model_dump() for s in citation_sources],
            )

        logger.info(
            "Multi-doc QA query executed for %s: '%s' (searched: %d docs, retrieved: %d chunks, latency: %.1f ms, grounded: %s)",
            current_user.email,
            clean_query,
            documents_searched,
            len(contexts),
            total_latency_ms,
            rag_response.is_grounded,
        )

        return AskQuestionResponse(
            answer=rag_response.answer,
            sources=citation_sources,
            retrieved_chunks=len(contexts),
            documents_searched=documents_searched,
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
    # Verify document ownership if document_ids passed
    valid_doc_ids: Optional[List[str]] = None
    if request.document_ids:
        valid_doc_ids = []
        for doc_id in request.document_ids:
            doc = db.get_document(doc_id)
            if doc and doc.user_id == current_user.id:
                valid_doc_ids.append(doc_id)

    session = db.create_chat_session(
        user_id=current_user.id,
        title=request.title or "New Conversation",
        document_ids=valid_doc_ids,
    )
    bound_docs = db.get_session_documents(session.id)
    return ChatSessionItem(
        id=session.id,
        title=session.title,
        document_ids=bound_docs,
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
    items = []
    for s in sessions:
        bound_docs = db.get_session_documents(s.id)
        items.append(
            ChatSessionItem(
                id=s.id,
                title=s.title,
                document_ids=bound_docs,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )
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

    bound_docs = db.get_session_documents(session_id)
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
            document_ids=bound_docs,
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
