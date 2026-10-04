from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Processing status (e.g. completed, failed)")
    pages: int = Field(..., description="Total pages extracted")
    chunks: int = Field(..., description="Total chunks indexed in ChromaDB")


class DocumentItem(BaseModel):
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    pages: int = Field(..., description="Total pages")
    chunks: int = Field(..., description="Total chunks in vector store")
    status: str = Field(..., description="Processing status")
    file_size: int = Field(0, description="File size in bytes")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")


class DocumentListResponse(BaseModel):
    documents: List[DocumentItem]


class DocumentDetailResponse(BaseModel):
    id: str
    filename: str
    pages: int
    chunks: int
    status: str
    file_size: int
    file_path: str
    created_at: str


class DocumentDeleteResponse(BaseModel):
    message: str


class DocumentPageResponse(BaseModel):
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document original filename")
    page_number: int = Field(..., description="1-indexed page number")
    total_pages: int = Field(..., description="Total pages in document")
    text: str = Field(..., description="Clean extracted text for the specified page")
