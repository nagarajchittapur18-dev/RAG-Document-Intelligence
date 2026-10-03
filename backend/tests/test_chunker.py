import pytest
from app.services.chunker import DocumentChunker, DocumentChunk
from app.services.pdf_processor import ExtractedDocument, ExtractedPage


@pytest.fixture
def sample_extracted_document():
    # Long paragraph ~600 characters repeated
    long_para = (
        "Retrieval-Augmented Generation (RAG) is an AI framework for improving the quality of LLM responses "
        "by grounding the model on external sources of knowledge to supplement the model's internal representation. "
        "Implementing RAG into an LLM-based architecture has several benefits: it ensures that the model has access "
        "to the most current, reliable facts, and that users have access to the model's sources, in order to verify "
        "its claims for accuracy and provenance. In this paper, we explore how RAG architectures scale with large "
        "corpora of technical documentation and how different retrieval strategies impact generation faithfulness. "
    )
    
    return ExtractedDocument(
        filename="rag_survey.pdf",
        file_path="/uploads/rag_survey.pdf",
        page_count=2,
        total_characters=len(long_para) * 4,
        total_words=len((long_para * 4).split()),
        pages=[
            ExtractedPage(
                page_number=1,
                text=long_para * 2,
                char_count=len(long_para * 2),
                word_count=len((long_para * 2).split()),
            ),
            ExtractedPage(
                page_number=2,
                text=long_para * 2,
                char_count=len(long_para * 2),
                word_count=len((long_para * 2).split()),
            ),
        ],
    )


def test_chunker_initialization_validation():
    """Verify that invalid chunk parameters raise ValueError."""
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        DocumentChunker(chunk_size=0)

    with pytest.raises(ValueError, match="chunk_overlap cannot be negative"):
        DocumentChunker(chunk_size=1000, chunk_overlap=-10)

    with pytest.raises(ValueError, match="strictly less than chunk_size"):
        DocumentChunker(chunk_size=500, chunk_overlap=500)


def test_chunk_page_small_text_no_split():
    """Test that a short page fitting in chunk_size yields exactly 1 chunk."""
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=150)
    page = ExtractedPage(
        page_number=1,
        text="A brief introduction to neural networks and artificial intelligence.",
        char_count=70,
        word_count=9,
    )
    chunks = chunker.chunk_page(page, document_id="doc101", document_name="neural.pdf")

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "doc_doc101_p1_c0"
    assert chunks[0].page_number == 1
    assert chunks[0].page_chunk_index == 0
    assert chunks[0].document_id == "doc101"
    assert chunks[0].document_name == "neural.pdf"
    assert chunks[0].text == "A brief introduction to neural networks and artificial intelligence."


def test_chunk_document_metadata_preservation(sample_extracted_document):
    """Test that document-level chunking preserves page numbers and sequential indices."""
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    chunks = chunker.chunk_document(sample_extracted_document, document_id="test_42")

    assert len(chunks) > 2

    # Check consecutive global indexes
    for i, chunk in enumerate(chunks):
        assert chunk.global_chunk_index == i
        assert chunk.document_id == "test_42"
        assert chunk.document_name == "rag_survey.pdf"
        assert chunk.page_number in [1, 2]
        assert chunk.metadata["page_number"] == chunk.page_number
        assert chunk.metadata["document_id"] == "test_42"
        assert chunk.metadata["chunk_id"] == chunk.chunk_id
        assert len(chunk.text) <= 600  # Within acceptable boundary

    # Verify both pages are represented
    page1_chunks = [c for c in chunks if c.page_number == 1]
    page2_chunks = [c for c in chunks if c.page_number == 2]
    assert len(page1_chunks) >= 2
    assert len(page2_chunks) >= 2

    # Verify page chunk IDs
    assert page1_chunks[0].chunk_id == "doc_test_42_p1_c0"
    assert page1_chunks[1].chunk_id == "doc_test_42_p1_c1"
    assert page2_chunks[0].chunk_id == "doc_test_42_p2_c0"


def test_chunk_overlap_presence():
    """Verify that consecutive chunks share overlapping content."""
    text = (
        "Sentence Alpha establishes the foundation. "
        "Sentence Beta introduces the second core concept. "
        "Sentence Gamma introduces the third important concept. "
        "Sentence Delta concludes the discussion."
    )
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=40)
    page = ExtractedPage(page_number=1, text=text, char_count=len(text), word_count=len(text.split()))
    chunks = chunker.chunk_page(page, document_id="overlap_test", document_name="test.pdf")

    assert len(chunks) >= 2
    # Ensure there is common substring between consecutive chunks
    overlap_found = False
    words_chunk0 = set(chunks[0].text.split())
    words_chunk1 = set(chunks[1].text.split())
    common_words = words_chunk0.intersection(words_chunk1)
    assert len(common_words) > 0, "Consecutive chunks should have overlapping tokens"
