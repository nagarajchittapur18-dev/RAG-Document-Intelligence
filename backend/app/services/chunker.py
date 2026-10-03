import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.services.pdf_processor import ExtractedDocument, ExtractedPage

logger = logging.getLogger("ragmate.chunker")


class DocumentChunk(BaseModel):
    chunk_id: str = Field(..., description="Deterministic unique chunk identifier")
    document_id: str = Field(..., description="ID of the parent document")
    document_name: str = Field(..., description="Original filename of the document")
    page_number: int = Field(..., description="1-indexed page number where chunk originates")
    page_chunk_index: int = Field(..., description="0-indexed chunk counter within this specific page")
    global_chunk_index: int = Field(..., description="0-indexed global chunk sequence counter in document")
    text: str = Field(..., description="Sanitized chunk text content")
    char_count: int = Field(..., description="Character count of chunk text")
    word_count: int = Field(..., description="Word count of chunk text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary for vector store")


class DocumentChunker:
    """
    Configurable document chunking engine.
    Splits document pages into semantically cohesive chunks while preserving exact page provenance.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        separators: Optional[List[str]] = None,
    ):
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap cannot be negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively splits text using hierarchical separators until pieces fit within chunk_size.
        """
        final_chunks: List[str] = []
        separator = separators[-1]
        new_separators: List[str] = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1 :]
                break

        splits = text.split(separator) if separator else list(text)

        good_splits: List[str] = []
        for s in splits:
            if s:
                if len(s) < self.chunk_size:
                    good_splits.append(s)
                else:
                    if new_separators:
                        other_info = self._split_text(s, new_separators)
                        good_splits.extend(other_info)
                    else:
                        # Hard character slice if no more separators exist
                        for pos in range(0, len(s), self.chunk_size - self.chunk_overlap):
                            good_splits.append(s[pos : pos + self.chunk_size])

        # Merge small splits respecting chunk_size and chunk_overlap
        merged_chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for piece in good_splits:
            piece_len = len(piece) + (len(separator) if current_chunk else 0)

            if current_length + piece_len <= self.chunk_size:
                current_chunk.append(piece)
                current_length += piece_len
            else:
                if current_chunk:
                    joined = separator.join(current_chunk).strip()
                    if joined:
                        merged_chunks.append(joined)

                    # Calculate overlap tokens/pieces
                    overlap_chunk: List[str] = []
                    overlap_len = 0
                    for prev_piece in reversed(current_chunk):
                        if overlap_len + len(prev_piece) <= self.chunk_overlap:
                            overlap_chunk.insert(0, prev_piece)
                            overlap_len += len(prev_piece)
                        else:
                            break

                    current_chunk = overlap_chunk
                    current_length = sum(len(p) for p in current_chunk)

                current_chunk.append(piece)
                current_length += len(piece)

        if current_chunk:
            joined = separator.join(current_chunk).strip()
            if joined:
                merged_chunks.append(joined)

        return merged_chunks

    def chunk_page(
        self,
        page: ExtractedPage,
        document_id: str,
        document_name: str,
        start_global_index: int = 0,
    ) -> List[DocumentChunk]:
        """
        Chunks an individual page, preserving the page number and generating deterministic chunk IDs.
        """
        cleaned_text = page.text.strip()
        if not cleaned_text:
            return []

        # If page fits within chunk size, no split needed
        if len(cleaned_text) <= self.chunk_size:
            text_chunks = [cleaned_text]
        else:
            text_chunks = self._split_text(cleaned_text, self.separators)

        chunks: List[DocumentChunk] = []
        for page_chunk_idx, text_chunk in enumerate(text_chunks):
            text_content = text_chunk.strip()
            if not text_content:
                continue

            chunk_id = f"doc_{document_id}_p{page.page_number}_c{page_chunk_idx}"
            global_idx = start_global_index + len(chunks)

            metadata = {
                "document_id": str(document_id),
                "document_name": document_name,
                "page_number": page.page_number,
                "chunk_id": chunk_id,
                "page_chunk_index": page_chunk_idx,
                "global_chunk_index": global_idx,
                "char_count": len(text_content),
                "word_count": len(text_content.split()),
            }

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=str(document_id),
                    document_name=document_name,
                    page_number=page.page_number,
                    page_chunk_index=page_chunk_idx,
                    global_chunk_index=global_idx,
                    text=text_content,
                    char_count=len(text_content),
                    word_count=len(text_content.split()),
                    metadata=metadata,
                )
            )

        return chunks

    def chunk_document(
        self,
        extracted_doc: ExtractedDocument,
        document_id: str,
    ) -> List[DocumentChunk]:
        """
        Chunks an entire document across all pages.
        Maintains consecutive global_chunk_index while preserving page-wise metadata.
        """
        all_chunks: List[DocumentChunk] = []

        logger.info(
            "Chunking document '%s' (ID: %s) with size=%d, overlap=%d",
            extracted_doc.filename,
            document_id,
            self.chunk_size,
            self.chunk_overlap,
        )

        for page in extracted_doc.pages:
            page_chunks = self.chunk_page(
                page=page,
                document_id=document_id,
                document_name=extracted_doc.filename,
                start_global_index=len(all_chunks),
            )
            all_chunks.extend(page_chunks)

        logger.info(
            "Completed chunking for '%s': produced %d total chunks across %d pages",
            extracted_doc.filename,
            len(all_chunks),
            extracted_doc.page_count,
        )

        return all_chunks
