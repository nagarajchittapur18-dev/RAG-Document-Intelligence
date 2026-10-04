import io
from pathlib import Path
from unittest.mock import patch
import pytest
import pymupdf
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import SourceCitation
from app.schemas.document import DocumentPageResponse
from app.services.document_store import DatabaseManager
from app.services.gemini import (
    CitationSource,
    GeminiService,
    SAFE_FALLBACK_ANSWER,
    extract_snippet,
    sanitize_citations,
)
from app.services.pdf_processor import PDFProcessor
from app.services.vector_store import SearchResult


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_header_user_a(client):
    """Registers and authenticates User A, returning Authorization headers."""
    email = "researcher_a@testcitations.edu"
    client.post("/api/auth/register", json={"name": "Researcher A", "email": email, "password": "Password123!"})
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_header_user_b(client):
    """Registers and authenticates User B, returning Authorization headers."""
    email = "researcher_b@testcitations.edu"
    client.post("/api/auth/register", json={"name": "Researcher B", "email": email, "password": "Password123!"})
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_test_pdf_stream(pages_content: list[str]) -> io.BytesIO:
    """Creates an in-memory PDF stream using PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_content:
        page = doc.new_page(width=595, height=842)
        if text:
            page.insert_text((50, 72), text, fontsize=11)
    stream = io.BytesIO(doc.tobytes())
    doc.close()
    stream.seek(0)
    return stream


def test_snippet_extraction():
    """Verify extract_snippet preserves sentence boundaries and truncates sensibly."""
    short_text = "This is a short chunk of text under limit."
    assert extract_snippet(short_text) == short_text

    long_text = (
        "First sentence discussing machine learning architectures. "
        "Second sentence elaborating on self-attention mechanisms and encoder-decoder stacks. "
        "Third sentence reviewing empirical BLEU scores and benchmark performance in translation tasks. "
        "Fourth sentence introducing hyperparameter tuning details for learning rate scheduling. "
        "Fifth sentence wrapping up conclusions and future directions."
    )
    snippet = extract_snippet(long_text, target_len=250, max_len=300)
    assert len(snippet) <= 300
    assert snippet.endswith(".")
    assert "First sentence" in snippet


def test_citation_sanitization_rules():
    """Verify that hallucinated citations are stripped and valid citations are formatted cleanly."""
    valid_ids = {1, 2}

    # 1. Valid citation preserved
    ans1 = "The model achieves 95% accuracy [1] and outperforms baselines [2]."
    assert sanitize_citations(ans1, valid_ids) == ans1

    # 2. Hallucinated citation [999] stripped
    ans2 = "The model achieves 95% accuracy [1] and future work will explore scale [999]."
    cleaned2 = sanitize_citations(ans2, valid_ids)
    assert "[999]" not in cleaned2
    assert "[1]" in cleaned2
    assert cleaned2.endswith("explore scale.")

    # 3. Mixed valid and invalid inside one bracket [1, 999] -> [1]
    ans3 = "Multi-source evidence supports this claim [1, 999]."
    assert sanitize_citations(ans3, valid_ids) == "Multi-source evidence supports this claim [1]."

    # 4. Source prefix normalization: [Source 1] -> [1]
    ans4 = "According to previous studies [Source 1], transformers scale effectively."
    assert sanitize_citations(ans4, valid_ids) == "According to previous studies [1], transformers scale effectively."

    # 5. Empty valid IDs (fallback or no context) strips all bracketed numbers
    ans5 = "Here is an ungrounded claim [1] and another [2]."
    assert sanitize_citations(ans5, set()) == "Here is an ungrounded claim and another."


def test_pdf_processor_extract_page(tmp_path):
    """Verify PDFProcessor.extract_page extracts single page content accurately."""
    pdf_path = tmp_path / "test_doc.pdf"
    pages = [
        "Page One: Introduction to Deep Residual Networks.",
        "Page Two: Methodology and skip connection architecture.",
        "Page Three: ImageNet classification benchmark results.",
    ]
    doc = pymupdf.open()
    for text in pages:
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 72), text, fontsize=11)
    doc.save(str(pdf_path))
    doc.close()

    processor = PDFProcessor()
    
    # Test valid page extraction
    page2 = processor.extract_page(str(pdf_path), 2)
    assert page2.page_number == 2
    assert "Methodology" in page2.text
    assert page2.char_count > 0

    # Test out of range page numbers
    with pytest.raises(IndexError):
        processor.extract_page(str(pdf_path), 0)

    with pytest.raises(IndexError):
        processor.extract_page(str(pdf_path), 4)


def test_gemini_service_citation_ordering_and_sanitization():
    """Verify GeminiService constructs 1-indexed citations and sanitizes answer."""
    service = GeminiService(api_key="mock_key")
    contexts = [
        SearchResult(
            chunk_id="chunk_a",
            document_id="doc_1",
            document_name="PaperA.pdf",
            page_number=1,
            text="Paper A introduces residual learning to solve degradation in deep networks.",
            similarity_score=0.91,
        ),
        SearchResult(
            chunk_id="chunk_b",
            document_id="doc_2",
            document_name="PaperB.pdf",
            page_number=4,
            text="Paper B proves transformers with multi-head attention outperform recurrent units.",
            similarity_score=0.87,
        ),
    ]

    mock_llm_output = (
        "Residual learning solves degradation [1], while attention outperforms RNNs [2]. "
        "Also speculative claims with no source [99]."
    )

    with patch.object(service, "_call_gemini_api", return_value=mock_llm_output):
        response = service.generate_grounded_answer(
            question="Compare residual networks and transformers.",
            contexts=contexts,
        )

        assert response.is_grounded is True
        assert "[1]" in response.answer
        assert "[2]" in response.answer
        assert "[99]" not in response.answer
        assert len(response.sources) == 2
        assert response.sources[0].citation_id == 1
        assert response.sources[0].document_name == "PaperA.pdf"
        assert response.sources[0].relevance_score == 0.91
        assert response.sources[1].citation_id == 2
        assert response.sources[1].document_name == "PaperB.pdf"
        assert response.sources[1].relevance_score == 0.87


def test_page_endpoint_lifecycle_and_user_isolation(client, auth_header_user_a, auth_header_user_b):
    """
    Comprehensive test of GET /api/documents/{document_id}/pages/{page_number}:
    - User A uploads multi-page document.
    - User A can retrieve page 1 and page 2 text.
    - Out of range page numbers return 400.
    - User B cannot retrieve User A's pages (404 isolation).
    - Unauthenticated request returns 401.
    """
    # 1. User A uploads 2-page document
    pdf_stream = create_test_pdf_stream([
        "DocuRAG Citation Test Page 1: Abstract and Overview.",
        "DocuRAG Citation Test Page 2: Detailed Experimental Results.",
    ])
    upload_res = client.post(
        "/api/documents/upload",
        headers=auth_header_user_a,
        files={"file": ("evidence_test.pdf", pdf_stream, "application/pdf")},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # 2. User A fetches page 1
    page1_res = client.get(f"/api/documents/{doc_id}/pages/1", headers=auth_header_user_a)
    assert page1_res.status_code == 200
    page1_data = page1_res.json()
    assert page1_data["document_id"] == doc_id
    assert page1_data["document_name"] == "evidence_test.pdf"
    assert page1_data["page_number"] == 1
    assert page1_data["total_pages"] == 2
    assert "Abstract and Overview" in page1_data["text"]

    # 3. User A fetches page 2
    page2_res = client.get(f"/api/documents/{doc_id}/pages/2", headers=auth_header_user_a)
    assert page2_res.status_code == 200
    assert "Detailed Experimental Results" in page2_res.json()["text"]

    # 4. Out of bounds page requests
    invalid_page_res = client.get(f"/api/documents/{doc_id}/pages/5", headers=auth_header_user_a)
    assert invalid_page_res.status_code == 400
    assert "out of range" in invalid_page_res.json()["detail"].lower()

    zero_page_res = client.get(f"/api/documents/{doc_id}/pages/0", headers=auth_header_user_a)
    assert zero_page_res.status_code == 400

    # 5. User Isolation: User B attempts to access User A's document page
    user_b_res = client.get(f"/api/documents/{doc_id}/pages/1", headers=auth_header_user_b)
    assert user_b_res.status_code == 404

    # 6. Unauthenticated request rejected
    unauth_res = client.get(f"/api/documents/{doc_id}/pages/1")
    assert unauth_res.status_code == 401


def test_chat_session_citation_provenance_restoration(client, auth_header_user_a):
    """
    Verifies that citations generated during chat retain full provenance
    (citation_id, document_id, page_number, relevance_score, snippet)
    when the session history is reloaded.
    """
    # 1. Upload document
    pdf_stream = create_test_pdf_stream([
        "Provenance Test Page 1: Transformer architectures replace recurrent layers with multi-head attention.",
    ])
    up_res = client.post(
        "/api/documents/upload",
        headers=auth_header_user_a,
        files={"file": ("provenance_paper.pdf", pdf_stream, "application/pdf")},
    )
    doc_id = up_res.json()["document_id"]

    # 2. Create session
    sess_res = client.post(
        "/api/chat/sessions",
        headers=auth_header_user_a,
        json={"title": "Provenance Session", "document_ids": [doc_id]},
    )
    session_id = sess_res.json()["id"]

    # 3. Ask question in session with mocked Gemini answer containing [1]
    mock_answer = "Transformers replace recurrent layers using multi-head self-attention mechanisms [1]."
    with patch("app.api.chat.gemini_service._call_gemini_api", return_value=mock_answer):
        ask_res = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            headers=auth_header_user_a,
            json={"question": "What do transformers replace?"},
        )
        assert ask_res.status_code == 200
        data = ask_res.json()
        assert "[1]" in data["answer"]
        assert len(data["sources"]) > 0
        first_source = data["sources"][0]
        assert first_source["citation_id"] == 1
        assert first_source["document_name"] == "provenance_paper.pdf"
        assert first_source["page_number"] == 1
        assert first_source["relevance_score"] is not None
        assert len(first_source["snippet"]) > 0

    # 4. Fetch full session messages and verify sources are preserved in SQLite
    get_sess_res = client.get(f"/api/chat/sessions/{session_id}", headers=auth_header_user_a)
    assert get_sess_res.status_code == 200
    messages = get_sess_res.json()["messages"]
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    assert len(assistant_msgs) >= 1
    stored_sources = assistant_msgs[0]["sources"]
    assert len(stored_sources) > 0
    assert stored_sources[0]["citation_id"] == 1
    assert stored_sources[0]["document_id"] == doc_id
    assert stored_sources[0]["page_number"] == 1
    assert "relevance_score" in stored_sources[0]
    assert "snippet" in stored_sources[0]
