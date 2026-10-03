import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.schemas.chat import (
    AskQuestionRequest,
    AskQuestionResponse,
    SourceCitation,
)
from app.services.gemini import GeminiService
from app.services.retrieval import RetrievalService
from app.services.vector_store import VectorStore

logger = logging.getLogger("ragmate.api.chat")
router = APIRouter(prefix="/chat", tags=["Chat & QA"])

# Shared service instances
vector_store = VectorStore()
retrieval_service = RetrievalService(vector_store=vector_store)
gemini_service = GeminiService()


@router.post(
    "/ask",
    response_model=AskQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a document-grounded question",
    description="Embeds the user query, retrieves relevant chunks from ChromaDB, and generates an answer using Google Gemini with exact page citations.",
)
async def ask_question(request: AskQuestionRequest):
    clean_query = request.question.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    t_start = time.perf_counter()
    k = request.top_k or settings.TOP_K

    try:
        # Step 1: Retrieve context chunks using existing RetrievalService
        contexts = retrieval_service.retrieve(
            query=clean_query,
            top_k=k,
            document_ids=request.document_ids,
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

        logger.info(
            "QA query executed: '%s' (retrieved: %d chunks, latency: %.1f ms, grounded: %s)",
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
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing question '%s': %s", clean_query, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the answer. Please try again.",
        )
