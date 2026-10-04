import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import settings
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentItem,
    DocumentListResponse,
    DocumentPageResponse,
    DocumentUploadResponse,
)
from app.services.chunker import DocumentChunker
from app.services.document_store import DocumentStore, UserRecord
from app.services.pdf_processor import (
    CorruptPDFError,
    EmptyPDFError,
    OversizedPDFError,
    PDFProcessor,
    ScannedPDFError,
)
from app.services.vector_store import VectorStore
from app.utils.dependencies import get_current_user

logger = logging.getLogger("ragmate.api.documents")
router = APIRouter(prefix="/documents", tags=["Documents"])

# Shared service instances
pdf_processor = PDFProcessor(max_file_size_mb=settings.MAX_FILE_SIZE_MB)
chunker = DocumentChunker(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
vector_store = VectorStore()
document_store = DocumentStore()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a PDF document",
    description="Uploads a PDF, extracts page-by-page text, segments text into chunks, generates embeddings, and indexes chunks into ChromaDB.",
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserRecord = Depends(get_current_user),
):
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided in upload request.",
        )

    filename = file.filename
    clean_filename = Path(filename).name

    # Validate file extension
    if not clean_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    # Validate Content-Type header if provided
    if file.content_type and "pdf" not in file.content_type.lower() and file.content_type != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MIME type. Only application/pdf files are supported.",
        )

    # Generate unique document ID
    doc_id = uuid.uuid4().hex[:12]

    # Prepare storage directory
    upload_dir = Path(settings.UPLOAD_DIRECTORY)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / f"{doc_id}_{clean_filename}"

    # Read content and enforce file size constraints
    try:
        content = await file.read()
        file_size = len(content)

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed size ({settings.MAX_FILE_SIZE_MB} MB).",
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        with open(saved_path, "wb") as f:
            f.write(content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to write uploaded file to disk: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while saving uploaded document.",
        )

    # Process PDF through extraction, chunking, and embedding pipeline
    try:
        extracted = pdf_processor.extract_document(str(saved_path), filename=clean_filename)
        chunks = chunker.chunk_document(extracted, document_id=doc_id)
        vector_store.add_chunks(chunks, user_id=current_user.id)
        document_store.add_document(
            document_id=doc_id,
            user_id=current_user.id,
            filename=clean_filename,
            file_path=str(saved_path.resolve()),
            pages=extracted.page_count,
            chunks=len(chunks),
            file_size=file_size,
            status="completed",
        )

        logger.info(
            "Document '%s' successfully indexed for user %s (ID: %s, pages: %d, chunks: %d)",
            clean_filename,
            current_user.email,
            doc_id,
            extracted.page_count,
            len(chunks),
        )

        return DocumentUploadResponse(
            document_id=doc_id,
            filename=clean_filename,
            status="completed",
            pages=extracted.page_count,
            chunks=len(chunks),
        )

    except (CorruptPDFError, EmptyPDFError, ScannedPDFError, OversizedPDFError) as pdf_err:
        # Clean up disk file on failure
        if saved_path.exists():
            saved_path.unlink(missing_ok=True)
        logger.warning("PDF processing failed for '%s': %s", clean_filename, str(pdf_err))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(pdf_err),
        )
    except Exception as e:
        if saved_path.exists():
            saved_path.unlink(missing_ok=True)
        logger.error("Unexpected error processing document '%s': %s", clean_filename, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document pipeline.",
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all uploaded documents",
    description="Returns metadata for all documents owned by the authenticated user.",
)
async def list_documents(current_user: UserRecord = Depends(get_current_user)):
    docs = document_store.list_documents_for_user(current_user.id)
    items = [
        DocumentItem(
            id=d.id,
            filename=d.filename,
            pages=d.pages,
            chunks=d.chunks,
            status=d.status,
            file_size=d.file_size,
            created_at=d.created_at,
        )
        for d in docs
    ]
    return DocumentListResponse(documents=items)


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
    description="Retrieves status, page count, chunk count, and metadata for a specific document.",
)
async def get_document(
    document_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    doc = document_store.get_document(document_id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        pages=doc.pages,
        chunks=doc.chunks,
        status=doc.status,
        file_size=doc.file_size,
        file_path=doc.file_path,
        created_at=doc.created_at,
    )


@router.get(
    "/{document_id}/pages/{page_number}",
    response_model=DocumentPageResponse,
    summary="Get extracted text for a specific document page",
    description="Retrieves the verified, cleaned text content of a single page from a user-owned document for citation verification.",
)
async def get_document_page(
    document_id: str,
    page_number: int,
    current_user: UserRecord = Depends(get_current_user),
):
    doc = document_store.get_document(document_id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if page_number < 1 or (doc.pages > 0 and page_number > doc.pages):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page number {page_number} is out of range. Document has {doc.pages} pages.",
        )

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Underlying document file not found on disk.",
        )

    try:
        page_data = pdf_processor.extract_page(str(file_path), page_number)
        return DocumentPageResponse(
            document_id=doc.id,
            document_name=doc.filename,
            page_number=page_data.page_number,
            total_pages=doc.pages,
            text=page_data.text,
        )
    except IndexError as ie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ie),
        )
    except Exception as e:
        logger.error("Failed to extract page %d from document %s: %s", page_number, document_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read page content: {str(e)}",
        )


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document",
    description="Removes the PDF file from disk, purges its vector embeddings from ChromaDB, and removes metadata.",
)
async def delete_document(
    document_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    doc = document_store.get_document(document_id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # 1. Purge from ChromaDB
    try:
        vector_store.delete_document(document_id)
    except Exception as e:
        logger.warning("Error deleting ChromaDB entries for document %s: %s", document_id, e)

    # 2. Delete file from storage
    try:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.warning("Could not delete file %s from disk: %s", doc.file_path, e)

    # 3. Delete from document registry
    document_store.delete_document(document_id, user_id=current_user.id)

    logger.info("Successfully deleted document '%s' (ID: %s) for user %s", doc.filename, document_id, current_user.email)
    return DocumentDeleteResponse(message="Document deleted successfully")
