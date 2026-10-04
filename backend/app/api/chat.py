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
    RenameSessionRequest,
    SessionDocumentInfo,
    SessionMessageRequest,
    SourceCitation,
)
from app.services.document_store import DatabaseManager, UserRecord
from app.services.gemini import GeminiService
from app.services.query_rewriter import QueryRewriter
from app.services.retrieval import RetrievalService
from app.services.vector_store import VectorStore
from app.utils.dependencies import get_current_user

logger = logging.getLogger("ragmate.api.chat")
router = APIRouter(prefix="/chat", tags=["Chat & QA"])

# Shared service instances
vector_store = VectorStore()
retrieval_service = RetrievalService(vector_store=vector_store)
gemini_service = GeminiService()
query_rewriter = QueryRewriter()
db = DatabaseManager()


# =============================================================================
# CORE RAG QA PIPELINE
# =============================================================================

async def _process_chat_query(
    clean_query: str,
    active_session_id: Optional[str],
    requested_doc_ids: Optional[List[str]],
    top_k: Optional[int],
    current_user: UserRecord,
) -> AskQuestionResponse:
    """
    Executes the conversational RAG pipeline:
    1. Validates session and document ownership.
    2. Auto-generates chat title on first turn if session has default title.
    3. Resolves conversation history and contextual query rewriting.
    4. Executes multi-document balanced vector retrieval.
    5. Dispatches strictly grounded prompt to Google Gemini.
    6. Persists user question and assistant answer with provenance citations.
    """
    t_start = time.perf_counter()
    k = top_k or settings.FINAL_TOP_K

    # 1. Verify session ownership if active_session_id provided
    if active_session_id:
        session = db.get_chat_session(active_session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session '{active_session_id}' not found.",
            )

        # Auto-generate title if currently default
        if session.title in ("New Conversation", "", None):
            auto_title = query_rewriter.generate_chat_title(clean_query)
            db.update_session_title_if_default(active_session_id, auto_title)

    # 2. Determine and validate document scope
    valid_doc_ids: Optional[List[str]] = None
    if requested_doc_ids is not None and len(requested_doc_ids) > 0:
        # User explicitly supplied document IDs
        valid_doc_ids = []
        for doc_id in requested_doc_ids:
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
        # Restore active document scope bound to this session
        bound_doc_ids = db.get_session_documents(active_session_id, active_only=True)
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

    # 3. Load recent conversation history (up to CHAT_HISTORY_LIMIT)
    conversation_history = None
    if active_session_id:
        limit = getattr(settings, "CHAT_HISTORY_LIMIT", 10)
        raw_hist = db.get_messages_for_session(active_session_id, limit=limit)
        conversation_history = [{"role": m.role, "content": m.content} for m in raw_hist]

    # 4. Contextual query rewriting for retrieval
    document_names: List[str] = []
    if valid_doc_ids:
        for d_id in valid_doc_ids:
            d_rec = db.get_document(d_id)
            if d_rec:
                document_names.append(d_rec.filename)

    retrieval_query = query_rewriter.rewrite_query_for_retrieval(
        question=clean_query,
        conversation_history=conversation_history,
        document_names=document_names,
    )

    try:
        # Step 5: Retrieve context chunks using multi-document balanced RetrievalService
        contexts = retrieval_service.retrieve(
            query=retrieval_query,
            top_k=k,
            document_ids=valid_doc_ids,
            user_id=current_user.id,
        )

        # Step 6: Synthesize grounded answer using GeminiService
        rag_response = gemini_service.generate_grounded_answer(
            question=clean_query,
            contexts=contexts,
            conversation_history=conversation_history,
        )

        total_latency_ms = (time.perf_counter() - t_start) * 1000

        # Step 7: Format deduplicated source citations
        seen_citations = set()
        citation_sources: List[SourceCitation] = []
        for s in rag_response.sources:
            cit_key = (s.document_id, s.chunk_id)
            if cit_key not in seen_citations:
                seen_citations.add(cit_key)
                citation_sources.append(
                    SourceCitation(
                        citation_id=getattr(s, "citation_id", len(citation_sources) + 1),
                        document_id=s.document_id,
                        document_name=s.document_name,
                        page_number=s.page_number,
                        chunk_id=s.chunk_id,
                        similarity_score=s.similarity_score,
                        relevance_score=getattr(s, "relevance_score", s.similarity_score),
                        snippet=s.snippet,
                    )
                )

        # Step 8: Persist messages in chat session if active
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
            "QA query executed for %s: '%s' (searched: %d docs, retrieved: %d chunks, latency: %.1f ms, grounded: %s)",
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

    return await _process_chat_query(
        clean_query=clean_query,
        active_session_id=request.session_id,
        requested_doc_ids=request.document_ids,
        top_k=request.top_k,
        current_user=current_user,
    )


# =============================================================================
# CHAT SESSION MANAGEMENT ENDPOINTS
# =============================================================================

@router.post(
    "/sessions",
    response_model=ChatSessionItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
    description="Initializes a new persistent chat session with optional document scoping.",
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

    title = request.title.strip() if request.title and request.title.strip() else "New Conversation"

    session = db.create_chat_session(
        user_id=current_user.id,
        title=title,
        document_ids=valid_doc_ids,
    )
    bound_docs = db.get_session_documents(session.id, active_only=True)
    return ChatSessionItem(
        id=session.id,
        title=session.title,
        document_ids=bound_docs,
        document_count=len(bound_docs),
        message_count=0,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
    summary="List all chat sessions for the current user",
    description="Returns all chat sessions owned by the authenticated user, ordered by updated_at descending with document and message counts.",
)
async def list_chat_sessions(current_user: UserRecord = Depends(get_current_user)):
    session_rows = db.list_chat_sessions_with_counts(current_user.id)
    items = []
    for s in session_rows:
        bound_docs = db.get_session_documents(s["id"], active_only=True)
        items.append(
            ChatSessionItem(
                id=s["id"],
                title=s["title"],
                document_ids=bound_docs,
                document_count=s.get("document_count", len(bound_docs)),
                message_count=s.get("message_count", 0),
                created_at=s["created_at"],
                updated_at=s["updated_at"],
            )
        )
    return ChatSessionListResponse(sessions=items)


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionMessagesResponse,
    summary="Get conversation history for a specific chat session",
    description="Loads session details, active bound documents, missing/deleted document detection, and message history.",
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

    # Fetch active document IDs
    bound_doc_ids = db.get_session_documents(session_id, active_only=True)

    # Populate active document info
    doc_info_list: List[SessionDocumentInfo] = []
    for doc_id in bound_doc_ids:
        doc = db.get_document(doc_id)
        if doc and doc.user_id == current_user.id:
            doc_info_list.append(
                SessionDocumentInfo(
                    id=doc.id,
                    name=doc.filename,
                    pages=doc.pages,
                    status=doc.status,
                )
            )

    # Check for unavailable/deleted documents
    unavailable_count = db.get_unavailable_documents_count(session_id)
    warning_message = None
    if unavailable_count > 0:
        warning_message = (
            f"{unavailable_count} document(s) previously used in this conversation "
            f"are no longer available."
        )

    # Fetch messages (ordered chronologically)
    limit = getattr(settings, "CHAT_MESSAGE_PAGE_SIZE", 50)
    raw_messages = db.get_messages_for_session(session_id, limit=limit)
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
            document_ids=bound_doc_ids,
            document_count=len(doc_info_list),
            message_count=len(messages),
            created_at=session.created_at,
            updated_at=session.updated_at,
        ),
        documents=doc_info_list,
        unavailable_documents_count=unavailable_count,
        warning_message=warning_message,
        messages=messages,
    )


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionItem,
    summary="Rename a chat session",
    description="Updates the title of an existing chat session owned by the authenticated user.",
)
async def rename_chat_session(
    session_id: str,
    request: RenameSessionRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    clean_title = request.title.strip()
    if not clean_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty.",
        )

    updated_session = db.rename_chat_session(session_id, current_user.id, clean_title)
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    bound_docs = db.get_session_documents(session_id, active_only=True)
    raw_messages = db.get_messages_for_session(session_id)
    return ChatSessionItem(
        id=updated_session.id,
        title=updated_session.title,
        document_ids=bound_docs,
        document_count=len(bound_docs),
        message_count=len(raw_messages),
        created_at=updated_session.created_at,
        updated_at=updated_session.updated_at,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a chat session and its history",
    description="Deletes the chat session, associated messages, and session-document links without affecting PDF documents or ChromaDB vectors.",
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


@router.post(
    "/sessions/{session_id}/messages",
    response_model=AskQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a question to a specific chat session",
    description="Sends a follow-up question inside an active chat session, utilizing recent conversation memory to resolve references and produce a grounded answer.",
)
async def send_session_message(
    session_id: str,
    request: SessionMessageRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    clean_query = request.question.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    return await _process_chat_query(
        clean_query=clean_query,
        active_session_id=session_id,
        requested_doc_ids=None,  # Uses bound session document scope
        top_k=request.top_k,
        current_user=current_user,
    )
