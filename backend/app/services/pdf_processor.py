import os
import re
import logging
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
import pymupdf

logger = logging.getLogger("ragmate.pdf_processor")


class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""
    pass


class OversizedPDFError(PDFProcessingError):
    """Raised when the PDF file size exceeds the configured limit."""
    pass


class CorruptPDFError(PDFProcessingError):
    """Raised when the file is not a valid PDF or is corrupted."""
    pass


class EmptyPDFError(PDFProcessingError):
    """Raised when the PDF has 0 pages or contains no extractable text."""
    pass


class ScannedPDFError(PDFProcessingError):
    """Raised when the PDF contains pages but zero extractable text (e.g. scanned image PDF)."""
    pass


class ExtractedPage(BaseModel):
    page_number: int = Field(..., description="1-indexed page number")
    text: str = Field(..., description="Cleaned, normalized page text")
    char_count: int = Field(..., description="Character count after cleaning")
    word_count: int = Field(..., description="Word count after cleaning")


class ExtractedDocument(BaseModel):
    filename: str
    file_path: str
    page_count: int
    total_characters: int
    total_words: int
    pages: List[ExtractedPage]


class PDFProcessor:
    """
    Robust, upload-independent PDF processing engine.
    Extracts text page-by-page using PyMuPDF, cleans text, and verifies extractability.
    """

    def __init__(self, max_file_size_mb: int = 25):
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def clean_text(self, raw_text: str) -> str:
        """
        Cleans and standardizes raw extracted text:
        1. Strips null bytes and non-printable control characters.
        2. Fixes hyphenated line breaks (e.g., 'trans-\nformer' -> 'transformer').
        3. Normalizes irregular whitespace and tabs while preserving paragraph breaks.
        4. Trims leading and trailing whitespace.
        """
        if not raw_text:
            return ""

        # Remove null characters and non-printable characters except whitespace
        text = raw_text.replace("\x00", " ")
        text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Fix hyphenated words broken across lines: word-\nword -> wordword
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

        # Standardize Windows/Mac newlines to \n
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace excessive consecutive horizontal spaces/tabs with single space
        text = re.sub(r"[ \t]+", " ", text)

        # Standardize vertical whitespace: collapse 3+ newlines to 2 (paragraph break)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

        return text.strip()

    def validate_file(self, file_path: str) -> Path:
        """
        Validates file existence, format signature, and file size.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        if file_size > self.max_file_size_bytes:
            raise OversizedPDFError(
                f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed limit ({self.max_file_size_mb} MB)."
            )

        if file_size == 0:
            raise CorruptPDFError("File is completely empty (0 bytes).")

        # Verify PDF magic bytes (%PDF-)
        try:
            with open(path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    raise CorruptPDFError(f"Invalid PDF header: {header}. Not a valid PDF document.")
        except IOError as e:
            raise CorruptPDFError(f"Could not read file header: {e}")

        return path

    def extract_document(self, file_path: str, filename: Optional[str] = None) -> ExtractedDocument:
        """
        Extracts text page-by-page from a PDF document.
        Preserves 1-indexed page numbers and performs text cleaning.
        """
        path = self.validate_file(file_path)
        doc_filename = filename or path.name

        logger.info("Starting text extraction for document: %s (%s)", doc_filename, file_path)

        try:
            doc = pymupdf.open(str(path))
        except Exception as e:
            logger.error("Failed to open PDF %s: %s", doc_filename, str(e))
            raise CorruptPDFError(f"Failed to parse PDF with PyMuPDF: {str(e)}")

        try:
            if doc.is_encrypted:
                raise CorruptPDFError(
                    f"Document '{doc_filename}' is password-protected or encrypted. "
                    "Encrypted PDFs are not supported."
                )

            page_count = len(doc)
            if page_count == 0:
                raise EmptyPDFError(f"Document '{doc_filename}' has 0 pages.")

            extracted_pages: List[ExtractedPage] = []
            total_chars = 0
            total_words = 0

            for page_idx in range(page_count):
                page = doc[page_idx]
                page_num = page_idx + 1  # 1-indexed page number

                raw_text = page.get_text("text") or ""
                cleaned = self.clean_text(raw_text)

                words = cleaned.split()
                char_count = len(cleaned)
                word_count = len(words)

                total_chars += char_count
                total_words += word_count

                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=cleaned,
                        char_count=char_count,
                        word_count=word_count,
                    )
                )

            # Check if all pages have 0 extractable text (scanned PDF image)
            if total_chars == 0 or total_words == 0:
                raise ScannedPDFError(
                    f"Document '{doc_filename}' contains {page_count} pages but no extractable text was found. "
                    "It appears to be a scanned document or image-only PDF."
                )

            logger.info(
                "Successfully extracted %s: %d pages, %d words, %d characters",
                doc_filename,
                page_count,
                total_words,
                total_chars,
            )

            return ExtractedDocument(
                filename=doc_filename,
                file_path=str(path.resolve()),
                page_count=page_count,
                total_characters=total_chars,
                total_words=total_words,
                pages=extracted_pages,
            )

        finally:
            doc.close()

    def extract_page(self, file_path: str, page_number: int) -> ExtractedPage:
        """
        Extracts and cleans text from a specific 1-indexed page of a PDF document.
        Raises IndexError if page_number is out of range.
        """
        path = self.validate_file(file_path)

        try:
            doc = pymupdf.open(str(path))
        except Exception as e:
            logger.error("Failed to open PDF %s: %s", path.name, str(e))
            raise CorruptPDFError(f"Failed to parse PDF with PyMuPDF: {str(e)}")

        try:
            if doc.is_encrypted:
                raise CorruptPDFError("Document is password-protected or encrypted.")

            page_count = len(doc)
            if page_number < 1 or page_number > page_count:
                raise IndexError(f"Page number {page_number} is out of range (1 to {page_count}).")

            page = doc[page_number - 1]
            raw_text = page.get_text("text") or ""
            cleaned = self.clean_text(raw_text)

            words = cleaned.split()
            char_count = len(cleaned)
            word_count = len(words)

            return ExtractedPage(
                page_number=page_number,
                text=cleaned,
                char_count=char_count,
                word_count=word_count,
            )
        finally:
            doc.close()
