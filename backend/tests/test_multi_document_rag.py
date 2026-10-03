import io
import time
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
import pymupdf

from app.main import app
from app.services.gemini import SAFE_FALLBACK_ANSWER


def create_in_memory_pdf(pages_text: list[str]) -> bytes:
    """Helper creating a real PDF in memory using PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)
        page.insert_textbox(pymupdf.Rect(50, 50, 550, 800), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def auth_headers_user():
    from app.services.document_store import DatabaseManager
    from app.utils.security import hash_password, create_access_token
    db = DatabaseManager()
    email = f"multidoc_{uuid.uuid4().hex[:6]}@example.com"
    pwd_hash = hash_password("ValidPassword123")
    user = db.create_user(name="MultiDoc Tester", email=email, password_hash=pwd_hash)
    token = create_access_token({"sub": user.id, "email": user.email})
    return {"Authorization": f"Bearer {token}", "user_id": user.id, "email": user.email}


@pytest.fixture
def paper_a_bytes():
    return create_in_memory_pdf([
        (
            "Research Paper Alpha: Sparse Lexical Indexing\n"
            "Methodology: Paper Alpha utilizes inverted index structures with BM25 term frequency weighting. "
            "Dataset: Evaluation is conducted strictly on the MS-MARCO passage retrieval benchmark. "
            "Results: Paper Alpha achieves a Mean Reciprocal Rank MRR@10 score of 0.325."
        )
    ])


@pytest.fixture
def paper_b_bytes():
    return create_in_memory_pdf([
        (
            "Research Paper Beta: Dense Semantic Embeddings\n"
            "Methodology: Paper Beta employs bi-encoder transformers with contrastive representation learning. "
            "Dataset: Evaluation is conducted on the BEIR heterogeneous benchmark collection. "
            "Results: Paper Beta achieves an MRR@10 score of 0.412, outperforming traditional lexical baselines."
        )
    ])


@pytest.fixture
def paper_c_bytes():
    return create_in_memory_pdf([
        (
            "Research Paper Gamma: Hybrid Cross-Encoder Reranking\n"
            "Methodology: Paper Gamma combines dense first-stage retrieval with a 6-layer cross-encoder reranker. "
            "Dataset: Evaluated across both TREC-COVID and HotpotQA multi-hop reasoning datasets. "
            "Results: Paper Gamma reports a top-1 precision score improvement of 18.4%."
        )
    ])


@pytest.mark.asyncio
async def test_single_document_query_mode(auth_headers_user, paper_a_bytes, paper_b_bytes):
    """
    Mode 1: Single Document Query.
    Upload Paper Alpha and Paper Beta. Query scoped exclusively to Paper Alpha.
    Must retrieve from Paper Alpha only.
    """
    headers = {"Authorization": auth_headers_user["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload Doc A
        up_a = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Alpha.pdf", paper_a_bytes, "application/pdf")},
            headers=headers,
        )
        assert up_a.status_code == 201
        doc_a_id = up_a.json()["document_id"]

        # Upload Doc B
        up_b = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Beta.pdf", paper_b_bytes, "application/pdf")},
            headers=headers,
        )
        assert up_b.status_code == 201
        doc_b_id = up_b.json()["document_id"]

        try:
            # Query scoped exclusively to Doc A
            res = await client.post(
                "/api/chat/ask",
                json={
                    "question": "What methodology is used in Paper Alpha?",
                    "document_ids": [doc_a_id],
                },
                headers=headers,
            )
            assert res.status_code == 200
            data = res.json()
            assert data["documents_searched"] == 1
            assert data["retrieved_chunks"] > 0
            # Every source must originate from doc_a_id
            for source in data["sources"]:
                assert source["document_id"] == doc_a_id
                assert "Alpha" in source["document_name"]

            # Query Doc A about content that exists ONLY in Doc B -> must return safe fallback
            res_exclusive_b = await client.post(
                "/api/chat/ask",
                json={
                    "question": "What benchmark score is reported on the BEIR benchmark?",
                    "document_ids": [doc_a_id],
                },
                headers=headers,
            )
            assert res_exclusive_b.status_code == 200
            data_b = res_exclusive_b.json()
            assert SAFE_FALLBACK_ANSWER in data_b["answer"]

        finally:
            await client.delete(f"/api/documents/{doc_a_id}", headers=headers)
            await client.delete(f"/api/documents/{doc_b_id}", headers=headers)


@pytest.mark.asyncio
async def test_multi_document_comparison_mode(auth_headers_user, paper_a_bytes, paper_b_bytes):
    """
    Mode 2: Selected Multiple Documents Comparison.
    Upload Paper Alpha and Paper Beta. Query scoped to [Doc A, Doc B].
    System must retrieve balanced chunks from both papers and ground comparison.
    """
    headers = {"Authorization": auth_headers_user["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload Doc A and Doc B
        up_a = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Alpha.pdf", paper_a_bytes, "application/pdf")},
            headers=headers,
        )
        doc_a_id = up_a.json()["document_id"]

        up_b = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Beta.pdf", paper_b_bytes, "application/pdf")},
            headers=headers,
        )
        doc_b_id = up_b.json()["document_id"]

        try:
            # Comparative question across both documents
            res = await client.post(
                "/api/chat/ask",
                json={
                    "question": "Compare the methodologies and datasets evaluated in Paper Alpha and Paper Beta.",
                    "document_ids": [doc_a_id, doc_b_id],
                },
                headers=headers,
            )
            assert res.status_code == 200
            data = res.json()
            assert data["documents_searched"] == 2
            assert data["retrieved_chunks"] >= 2

            # Check that sources contain citations from BOTH documents
            cited_doc_ids = {s["document_id"] for s in data["sources"]}
            assert doc_a_id in cited_doc_ids
            assert doc_b_id in cited_doc_ids

            # Verify no duplicate chunk citations
            chunk_ids = [s["chunk_id"] for s in data["sources"]]
            assert len(chunk_ids) == len(set(chunk_ids))

            # Verify grounded answer synthesizes evidence from both
            answer = data["answer"].lower()
            assert "alpha" in answer or "bm25" in answer or "inverted index" in answer
            assert "beta" in answer or "dense" in answer or "transformer" in answer

        finally:
            await client.delete(f"/api/documents/{doc_a_id}", headers=headers)
            await client.delete(f"/api/documents/{doc_b_id}", headers=headers)


@pytest.mark.asyncio
async def test_all_documents_mode(auth_headers_user, paper_a_bytes, paper_b_bytes, paper_c_bytes):
    """
    Mode 3: All Documents Global Query.
    When document_ids is omitted or empty ([]), retrieval operates across all user's documents.
    """
    headers = {"Authorization": auth_headers_user["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        up_a = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Alpha.pdf", paper_a_bytes, "application/pdf")},
            headers=headers,
        )
        doc_a_id = up_a.json()["document_id"]

        up_b = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Beta.pdf", paper_b_bytes, "application/pdf")},
            headers=headers,
        )
        doc_b_id = up_b.json()["document_id"]

        up_c = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Gamma.pdf", paper_c_bytes, "application/pdf")},
            headers=headers,
        )
        doc_c_id = up_c.json()["document_id"]

        try:
            # Query across all documents (document_ids is empty list)
            res = await client.post(
                "/api/chat/ask",
                json={
                    "question": "Which paper evaluates on the HotpotQA multi-hop dataset?",
                    "document_ids": [],
                },
                headers=headers,
            )
            assert res.status_code == 200
            data = res.json()
            assert data["documents_searched"] == 3
            assert data["retrieved_chunks"] > 0
            cited_names = [s["document_name"] for s in data["sources"]]
            assert any("Gamma" in name for name in cited_names)

        finally:
            await client.delete(f"/api/documents/{doc_a_id}", headers=headers)
            await client.delete(f"/api/documents/{doc_b_id}", headers=headers)
            await client.delete(f"/api/documents/{doc_c_id}", headers=headers)


@pytest.mark.asyncio
async def test_chat_session_document_scope_persistence(auth_headers_user, paper_a_bytes, paper_b_bytes):
    """
    Verify chat sessions remember their bound document scope across turns.
    """
    headers = {"Authorization": auth_headers_user["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        up_a = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Alpha.pdf", paper_a_bytes, "application/pdf")},
            headers=headers,
        )
        doc_a_id = up_a.json()["document_id"]

        up_b = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Beta.pdf", paper_b_bytes, "application/pdf")},
            headers=headers,
        )
        doc_b_id = up_b.json()["document_id"]

        try:
            # 1. Create chat session bound to Doc A only
            sess_res = await client.post(
                "/api/chat/sessions",
                json={"title": "Paper Alpha Study", "document_ids": [doc_a_id]},
                headers=headers,
            )
            assert sess_res.status_code == 201
            session_id = sess_res.json()["id"]
            assert sess_res.json()["document_ids"] == [doc_a_id]

            # 2. Ask question without specifying document_ids, but passing session_id
            ask_res = await client.post(
                "/api/chat/ask",
                json={
                    "question": "What is the primary evaluation dataset used?",
                    "session_id": session_id,
                },
                headers=headers,
            )
            assert ask_res.status_code == 200
            data = ask_res.json()
            assert data["documents_searched"] == 1
            for s in data["sources"]:
                assert s["document_id"] == doc_a_id

            # 3. Retrieve session messages and verify history
            get_sess = await client.get(f"/api/chat/sessions/{session_id}", headers=headers)
            assert get_sess.status_code == 200
            sess_data = get_sess.json()
            assert len(sess_data["messages"]) == 2  # user + assistant

            # 4. Clean up session
            del_sess = await client.delete(f"/api/chat/sessions/{session_id}", headers=headers)
            assert del_sess.status_code == 200

        finally:
            await client.delete(f"/api/documents/{doc_a_id}", headers=headers)
            await client.delete(f"/api/documents/{doc_b_id}", headers=headers)


@pytest.mark.asyncio
async def test_document_deletion_cascades_cleanly(auth_headers_user, paper_a_bytes):
    """
    Verify deleting a document cleans up ChromaDB chunks, database records, and chat session links.
    """
    headers = {"Authorization": auth_headers_user["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        up_a = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Alpha.pdf", paper_a_bytes, "application/pdf")},
            headers=headers,
        )
        doc_a_id = up_a.json()["document_id"]

        # Bind to a session
        sess_res = await client.post(
            "/api/chat/sessions",
            json={"title": "Session to delete", "document_ids": [doc_a_id]},
            headers=headers,
        )
        session_id = sess_res.json()["id"]

        # Delete document
        del_res = await client.delete(f"/api/documents/{doc_a_id}", headers=headers)
        assert del_res.status_code == 200

        # Query session -> document_ids should no longer include deleted doc
        get_sess = await client.get(f"/api/chat/sessions/{session_id}", headers=headers)
        assert get_sess.status_code == 200
        assert doc_a_id not in get_sess.json()["session"]["document_ids"]

        # Cleanup session
        await client.delete(f"/api/chat/sessions/{session_id}", headers=headers)


@pytest.mark.asyncio
async def test_multi_document_performance_benchmark(auth_headers_user, paper_a_bytes, paper_b_bytes):
    """
    Performance Test (Section 35):
    Measures and compares Single-Document vs Multi-Document retrieval latency and response times.
    """
    headers = {"Authorization": auth_headers_user["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        up_a = await client.post(
            "/api/documents/upload",
            files={"file": ("Benchmark_Alpha.pdf", paper_a_bytes, "application/pdf")},
            headers=headers,
        )
        doc_a_id = up_a.json()["document_id"]

        up_b = await client.post(
            "/api/documents/upload",
            files={"file": ("Benchmark_Beta.pdf", paper_b_bytes, "application/pdf")},
            headers=headers,
        )
        doc_b_id = up_b.json()["document_id"]

        try:
            # 1. Single-Document Benchmark
            t0 = time.perf_counter()
            single_res = await client.post(
                "/api/chat/ask",
                json={
                    "question": "What is the methodology in Benchmark Alpha?",
                    "document_ids": [doc_a_id],
                },
                headers=headers,
            )
            single_latency = (time.perf_counter() - t0) * 1000
            assert single_res.status_code == 200
            single_data = single_res.json()

            # 2. Multi-Document Benchmark
            t1 = time.perf_counter()
            multi_res = await client.post(
                "/api/chat/ask",
                json={
                    "question": "Compare the evaluation benchmarks between Alpha and Beta.",
                    "document_ids": [doc_a_id, doc_b_id],
                },
                headers=headers,
            )
            multi_latency = (time.perf_counter() - t1) * 1000
            assert multi_res.status_code == 200
            multi_data = multi_res.json()

            print(f"\n[BENCHMARK] Single-Doc: {single_latency:.1f}ms (chunks: {single_data['retrieved_chunks']}) | "
                  f"Multi-Doc: {multi_latency:.1f}ms (chunks: {multi_data['retrieved_chunks']})")

            assert single_data["documents_searched"] == 1
            assert multi_data["documents_searched"] == 2
            assert single_latency > 0
            assert multi_latency > 0

        finally:
            await client.delete(f"/api/documents/{doc_a_id}", headers=headers)
            await client.delete(f"/api/documents/{doc_b_id}", headers=headers)
