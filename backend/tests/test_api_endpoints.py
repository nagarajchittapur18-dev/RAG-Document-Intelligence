import io
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
import pymupdf

from app.main import app
from app.services.gemini import SAFE_FALLBACK_ANSWER


def create_in_memory_pdf(pages_text: list[str]) -> bytes:
    """Helper creating a real PDF in memory using PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 72), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_pdf_bytes():
    return create_in_memory_pdf([
        (
            "DocuRAG Research Paper\n"
            "Section 1: Architecture\n"
            "DocuRAG uses a dense semantic retrieval pipeline with sentence transformers and ChromaDB. "
            "It eliminates generative hallucinations through strict provenance-based prompt grounding."
        ),
        (
            "Section 2: Performance Evaluation\n"
            "Our benchmark demonstrates that page-level citation retention reduces citation errors by 45%. "
            "Mean response time across 100 queries is 780 milliseconds."
        ),
    ])


@pytest.fixture
def auth_headers():
    from app.services.document_store import DatabaseManager
    from app.utils.security import hash_password, create_access_token
    import uuid
    db = DatabaseManager()
    email = f"test_api_{uuid.uuid4().hex[:6]}@example.com"
    pwd_hash = hash_password("ValidPassword123")
    user = db.create_user(name="API Tester", email=email, password_hash=pwd_hash)
    token = create_access_token({"sub": user.id, "email": user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Verify GET /api/health."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "DocuRAG API"


@pytest.mark.asyncio
async def test_upload_invalid_extension(auth_headers):
    """Verify POST /api/documents/upload rejects non-PDF files."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("test.txt", b"plain text", "text/plain")}
        response = await client.post("/api/documents/upload", files=files, headers=auth_headers)
        assert response.status_code == 400
        assert "Only PDF files are supported" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_empty_pdf(auth_headers):
    """Verify POST /api/documents/upload rejects empty files."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        response = await client.post("/api/documents/upload", files=files, headers=auth_headers)
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_full_document_lifecycle_and_qa(sample_pdf_bytes, auth_headers):
    """
    End-to-End Test:
    Upload PDF -> List Docs -> Get Details -> Ask Grounded Question -> Ask Fallback Question -> Delete Doc.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload valid 2-page PDF
        files = {"file": ("docurag_paper.pdf", sample_pdf_bytes, "application/pdf")}
        upload_resp = await client.post("/api/documents/upload", files=files, headers=auth_headers)
        assert upload_resp.status_code == 201
        upload_data = upload_resp.json()
        doc_id = upload_data["document_id"]
        assert upload_data["filename"] == "docurag_paper.pdf"
        assert upload_data["status"] == "completed"
        assert upload_data["pages"] == 2
        assert upload_data["chunks"] >= 2

        try:
            # 2. List documents
            list_resp = await client.get("/api/documents", headers=auth_headers)
            assert list_resp.status_code == 200
            list_data = list_resp.json()
            doc_ids = [d["id"] for d in list_data["documents"]]
            assert doc_id in doc_ids

            # 3. Get document details
            detail_resp = await client.get(f"/api/documents/{doc_id}", headers=auth_headers)
            assert detail_resp.status_code == 200
            detail_data = detail_resp.json()
            assert detail_data["id"] == doc_id
            assert detail_data["filename"] == "docurag_paper.pdf"
            assert detail_data["pages"] == 2
            assert detail_data["status"] == "completed"

            # 4. Ask grounded question
            ask_resp = await client.post(
                "/api/chat/ask",
                json={
                    "question": "What is the percentage reduction in citation errors reported?",
                    "document_ids": [doc_id],
                },
                headers=auth_headers,
            )
            assert ask_resp.status_code == 200
            ask_data = ask_resp.json()
            assert len(ask_data["answer"]) > 10
            assert ask_data["retrieved_chunks"] > 0
            assert ask_data["response_time_ms"] > 0

            # 5. Ask out-of-context unanswerable question
            fallback_resp = await client.post(
                "/api/chat/ask",
                json={
                    "question": "What is the recipe for baking chocolate cookies?",
                    "document_ids": [doc_id],
                },
                headers=auth_headers,
            )
            assert fallback_resp.status_code == 200
            fallback_data = fallback_resp.json()
            assert SAFE_FALLBACK_ANSWER in fallback_data["answer"]

            # 6. Ask empty question (should return 400 Bad Request)
            empty_resp = await client.post(
                "/api/chat/ask",
                json={"question": "   ", "document_ids": [doc_id]},
                headers=auth_headers,
            )
            assert empty_resp.status_code == 400
            assert "cannot be empty" in empty_resp.json()["detail"].lower()

        finally:
            # 7. Delete document
            delete_resp = await client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
            assert delete_resp.status_code == 200
            assert "deleted successfully" in delete_resp.json()["message"].lower()

            # 8. Verify document is gone
            get_after_delete = await client.get(f"/api/documents/{doc_id}", headers=auth_headers)
            assert get_after_delete.status_code == 404

            # 9. Verify deleting again returns 404
            delete_again = await client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
            assert delete_again.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_document(auth_headers):
    """Verify GET /api/documents/{id} returns 404 for unknown ID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/documents/non_existent_id_9999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
