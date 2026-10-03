import os
from pathlib import Path
import pytest
import pymupdf
from app.services.pdf_processor import (
    PDFProcessor,
    CorruptPDFError,
    EmptyPDFError,
    ScannedPDFError,
    OversizedPDFError,
)


@pytest.fixture
def processor():
    return PDFProcessor(max_file_size_mb=25)


@pytest.fixture
def temp_pdf_dir(tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    return pdf_dir


def create_sample_pdf(file_path: Path, pages_content: list[str]) -> Path:
    """Helper using PyMuPDF to programmatically generate test PDF documents."""
    doc = pymupdf.open()
    for text in pages_content:
        page = doc.new_page(width=595, height=842)  # A4 dimensions
        if text:
            # Insert text at top margin
            page.insert_text((50, 72), text, fontsize=11)
    doc.save(str(file_path))
    doc.close()
    return file_path


def test_text_cleaning(processor):
    """Test text cleaning for hyphenation, null bytes, and excessive whitespace."""
    raw = "The deep learn-\ning model uses self-\nattention mechanisms.\x00\n\n\n\nIt achieves high accuracy."
    cleaned = processor.clean_text(raw)
    
    assert "learning" in cleaned
    assert "selfattention" in cleaned or "self" in cleaned
    assert "\x00" not in cleaned
    assert "\n\n\n" not in cleaned
    assert "It achieves high accuracy." in cleaned


def test_valid_multipage_pdf_extraction(processor, temp_pdf_dir):
    """Test extracting a valid 3-page academic paper PDF."""
    pdf_path = temp_pdf_dir / "valid_paper.pdf"
    pages = [
        "Title: Attention Mechanism in Transformer Networks\nAuthor: Academic Team\nAbstract: This paper studies self-attention.",
        "Section 2: Methodology\nThe model consists of an encoder and decoder stack with 6 identical layers.",
        "Section 3: Experimental Results\nTable 1 demonstrates BLEU scores on WMT 2014 English-to-German benchmarks.",
    ]
    create_sample_pdf(pdf_path, pages)

    extracted = processor.extract_document(str(pdf_path))

    assert extracted.filename == "valid_paper.pdf"
    assert extracted.page_count == 3
    assert len(extracted.pages) == 3

    assert extracted.pages[0].page_number == 1
    assert "Attention Mechanism" in extracted.pages[0].text
    assert extracted.pages[0].word_count > 5

    assert extracted.pages[1].page_number == 2
    assert "Methodology" in extracted.pages[1].text

    assert extracted.pages[2].page_number == 3
    assert "Experimental Results" in extracted.pages[2].text

    assert extracted.total_characters > 100
    assert extracted.total_words > 20


def test_missing_file_raises_error(processor):
    """Test that non-existent PDF file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        processor.extract_document("non_existent_file.pdf")


def test_corrupt_non_pdf_file(processor, temp_pdf_dir):
    """Test that a non-PDF file (invalid magic bytes) raises CorruptPDFError."""
    fake_pdf = temp_pdf_dir / "fake.pdf"
    fake_pdf.write_text("This is plain text without PDF signature header.")

    with pytest.raises(CorruptPDFError):
        processor.extract_document(str(fake_pdf))


def test_empty_zero_byte_file(processor, temp_pdf_dir):
    """Test that a 0-byte file raises CorruptPDFError."""
    empty_file = temp_pdf_dir / "zero.pdf"
    empty_file.write_bytes(b"")

    with pytest.raises(CorruptPDFError):
        processor.extract_document(str(empty_file))


def test_scanned_image_pdf_raises_error(processor, temp_pdf_dir):
    """Test that a PDF with blank pages (no extractable text) raises ScannedPDFError."""
    scanned_pdf = temp_pdf_dir / "scanned.pdf"
    # Create 2 pages with zero text content
    create_sample_pdf(scanned_pdf, ["", ""])

    with pytest.raises(ScannedPDFError):
        processor.extract_document(str(scanned_pdf))


def test_oversized_pdf_raises_error(temp_pdf_dir):
    """Test that a PDF exceeding max_file_size_mb raises OversizedPDFError."""
    # Set limit to 0.001 MB (~1 KB)
    strict_processor = PDFProcessor(max_file_size_mb=0)
    strict_processor.max_file_size_bytes = 100  # 100 bytes limit

    pdf_path = temp_pdf_dir / "large.pdf"
    create_sample_pdf(pdf_path, ["This is a regular page with text content."])

    with pytest.raises(OversizedPDFError):
        strict_processor.extract_document(str(pdf_path))
