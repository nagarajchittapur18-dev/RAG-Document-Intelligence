import uuid
import pytest
from httpx import ASGITransport, AsyncClient
import pymupdf

from app.main import app
from app.services.document_store import DatabaseManager
from app.services.gemini import SAFE_FALLBACK_ANSWER
from app.services.query_rewriter import QueryRewriter


def create_in_memory_pdf(pages_text: list[str]) -> bytes:
    """Helper creating a real PDF in memory using PyMuPDF with text wrapping."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)
        page.insert_textbox(pymupdf.Rect(50, 50, 550, 800), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def auth_user_a():
    from app.utils.security import create_access_token, hash_password
    db = DatabaseManager()
    email = f"user_a_{uuid.uuid4().hex[:6]}@example.com"
    user = db.create_user(name="User A", email=email, password_hash=hash_password("Pass123!"))
    token = create_access_token({"sub": user.id, "email": user.email})
    return {"Authorization": f"Bearer {token}", "user_id": user.id, "email": user.email}


@pytest.fixture
def auth_user_b():
    from app.utils.security import create_access_token, hash_password
    db = DatabaseManager()
    email = f"user_b_{uuid.uuid4().hex[:6]}@example.com"
    user = db.create_user(name="User B", email=email, password_hash=hash_password("Pass123!"))
    token = create_access_token({"sub": user.id, "email": user.email})
    return {"Authorization": f"Bearer {token}", "user_id": user.id, "email": user.email}


@pytest.fixture
def paper_alpha_bytes():
    return create_in_memory_pdf([
        (
            "Research Paper Alpha: Sparse Inverted Indexing\n"
            "Architecture and Methodology: Paper Alpha implements inverted indices with BM25 passage weighting. "
            "Evaluation Dataset: Experiments are strictly evaluated on the MS-MARCO benchmark dataset. "
            "Results: Paper Alpha reports an MRR@10 passage retrieval accuracy of 0.342."
        )
    ])


@pytest.fixture
def paper_beta_bytes():
    return create_in_memory_pdf([
        (
            "Research Paper Beta: Dense Representation Learning\n"
            "Architecture and Methodology: Paper Beta utilizes dual-encoder transformer representations with contrastive loss. "
            "Evaluation Dataset: Evaluated across the BEIR heterogeneous information retrieval benchmark suite. "
            "Results: Paper Beta achieves an accuracy improvement of 14.8% over traditional inverted indices."
        )
    ])


# =============================================================================
# 1. AUTHENTICATION & ACCESS CONTROL TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_sessions():
    """Unauthenticated requests must be rejected with HTTP 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/chat/sessions")
        assert res.status_code == 401

        res_post = await client.post("/api/chat/sessions", json={"title": "Test"})
        assert res_post.status_code == 401


# =============================================================================
# 2. SESSION LIFECYCLE TESTS (CREATE, LIST, GET, RENAME, DELETE)
# =============================================================================

@pytest.mark.asyncio
async def test_session_lifecycle(auth_user_a, paper_alpha_bytes):
    """
    Test complete session lifecycle:
    Create -> List (with counts) -> Get details -> Rename -> Delete.
    """
    headers = {"Authorization": auth_user_a["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload a document
        up_resp = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Alpha.pdf", paper_alpha_bytes, "application/pdf")},
            headers=headers,
        )
        assert up_resp.status_code == 201
        doc_id = up_resp.json()["document_id"]

        try:
            # 2. Create session with bound document
            create_resp = await client.post(
                "/api/chat/sessions",
                json={"title": "Paper Alpha Study", "document_ids": [doc_id]},
                headers=headers,
            )
            assert create_resp.status_code == 201
            session_data = create_resp.json()
            session_id = session_data["id"]
            assert session_data["title"] == "Paper Alpha Study"
            assert doc_id in session_data["document_ids"]

            # 3. List sessions
            list_resp = await client.get("/api/chat/sessions", headers=headers)
            assert list_resp.status_code == 200
            sessions_list = list_resp.json()["sessions"]
            matching = [s for s in sessions_list if s["id"] == session_id]
            assert len(matching) == 1
            assert matching[0]["document_count"] == 1
            assert matching[0]["message_count"] == 0

            # 4. Rename session
            rename_resp = await client.patch(
                f"/api/chat/sessions/{session_id}",
                json={"title": "Updated Paper Alpha Investigation"},
                headers=headers,
            )
            assert rename_resp.status_code == 200
            assert rename_resp.json()["title"] == "Updated Paper Alpha Investigation"

            # 5. Get session details
            get_resp = await client.get(f"/api/chat/sessions/{session_id}", headers=headers)
            assert get_resp.status_code == 200
            detail = get_resp.json()
            assert detail["session"]["title"] == "Updated Paper Alpha Investigation"
            assert len(detail["documents"]) == 1
            assert detail["documents"][0]["id"] == doc_id
            assert detail["unavailable_documents_count"] == 0
            assert detail["warning_message"] is None

            # 6. Delete session
            del_resp = await client.delete(f"/api/chat/sessions/{session_id}", headers=headers)
            assert del_resp.status_code == 200

            # 7. Verify session no longer exists
            get_del = await client.get(f"/api/chat/sessions/{session_id}", headers=headers)
            assert get_del.status_code == 404

            # 8. Verify the actual PDF document still exists (not deleted by session deletion)
            doc_check = await client.get(f"/api/documents/{doc_id}", headers=headers)
            assert doc_check.status_code == 200

        finally:
            await client.delete(f"/api/documents/{doc_id}", headers=headers)


# =============================================================================
# 3. USER DATA ISOLATION (SECTION 29)
# =============================================================================

@pytest.mark.asyncio
async def test_multi_tenant_chat_session_isolation(auth_user_a, auth_user_b):
    """
    Verify strict user data isolation:
    User A cannot read, rename, delete, or submit messages to User B's session.
    """
    headers_a = {"Authorization": auth_user_a["Authorization"]}
    headers_b = {"Authorization": auth_user_b["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # User B creates a session
        create_b = await client.post(
            "/api/chat/sessions",
            json={"title": "User B Confidential Session"},
            headers=headers_b,
        )
        assert create_b.status_code == 201
        session_b_id = create_b.json()["id"]

        try:
            # User A tries to get User B's session -> must return 404
            get_by_a = await client.get(f"/api/chat/sessions/{session_b_id}", headers=headers_a)
            assert get_by_a.status_code == 404

            # User A tries to rename User B's session -> must return 404
            rename_by_a = await client.patch(
                f"/api/chat/sessions/{session_b_id}",
                json={"title": "Hacked Title"},
                headers=headers_a,
            )
            assert rename_by_a.status_code == 404

            # User A tries to send a message to User B's session -> must return 404
            msg_by_a = await client.post(
                f"/api/chat/sessions/{session_b_id}/messages",
                json={"question": "What is in this session?"},
                headers=headers_a,
            )
            assert msg_by_a.status_code == 404

            # User A tries to delete User B's session -> must return 404
            del_by_a = await client.delete(f"/api/chat/sessions/{session_b_id}", headers=headers_a)
            assert del_by_a.status_code == 404

            # Verify session still intact for User B
            get_by_b = await client.get(f"/api/chat/sessions/{session_b_id}", headers=headers_b)
            assert get_by_b.status_code == 200
            assert get_by_b.json()["session"]["title"] == "User B Confidential Session"

        finally:
            await client.delete(f"/api/chat/sessions/{session_b_id}", headers=headers_b)


# =============================================================================
# 4. FOLLOW-UP QUESTION & CONVERSATION MEMORY TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_followup_question_and_title_autogen(auth_user_a, paper_alpha_bytes):
    """
    Test multi-turn conversation memory:
    Turn 1: 'What methodology does Paper Alpha implement?' -> Triggers title auto-generation.
    Turn 2: 'What dataset does it use for evaluation?' -> Follow-up using 'it'.
    Verifies that the system resolves the reference and answers from Paper Alpha's dataset section.
    """
    headers = {"Authorization": auth_user_a["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload Paper Alpha
        up_resp = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Alpha.pdf", paper_alpha_bytes, "application/pdf")},
            headers=headers,
        )
        doc_id = up_resp.json()["document_id"]

        # Create session with default title
        sess_resp = await client.post(
            "/api/chat/sessions",
            json={"title": "New Conversation", "document_ids": [doc_id]},
            headers=headers,
        )
        session_id = sess_resp.json()["id"]

        try:
            # Turn 1: First question
            turn1 = await client.post(
                f"/api/chat/sessions/{session_id}/messages",
                json={"question": "What architecture and methodology does Paper Alpha implement?"},
                headers=headers,
            )
            assert turn1.status_code == 200
            ans1 = turn1.json()
            assert ans1["retrieved_chunks"] > 0
            assert len(ans1["sources"]) > 0

            # Verify automatic title generation updated the title from 'New Conversation'
            sess_check = await client.get(f"/api/chat/sessions/{session_id}", headers=headers)
            assert sess_check.status_code == 200
            updated_title = sess_check.json()["session"]["title"]
            assert updated_title != "New Conversation"
            assert len(updated_title) > 3

            # Turn 2: Follow-up question with pronoun 'it'
            turn2 = await client.post(
                f"/api/chat/sessions/{session_id}/messages",
                json={"question": "What evaluation dataset does it use?"},
                headers=headers,
            )
            assert turn2.status_code == 200
            ans2 = turn2.json()
            assert ans2["retrieved_chunks"] > 0
            # Answer must reference MS-MARCO
            assert "ms-marco" in ans2["answer"].lower()

            # Verify message count in session
            sess_details = await client.get(f"/api/chat/sessions/{session_id}", headers=headers)
            assert sess_details.status_code == 200
            # 2 user messages + 2 assistant messages = 4 messages
            assert len(sess_details.json()["messages"]) == 4

        finally:
            await client.delete(f"/api/documents/{doc_id}", headers=headers)
            await client.delete(f"/api/chat/sessions/{session_id}", headers=headers)


# =============================================================================
# 5. DELETED DOCUMENT GRACEFUL HANDLING (SECTION 24)
# =============================================================================

@pytest.mark.asyncio
async def test_graceful_handling_of_deleted_document(auth_user_a, paper_alpha_bytes, paper_beta_bytes):
    """
    Test Section 24:
    A session is bound to Doc A and Doc B.
    Doc B is subsequently deleted.
    When the session is reopened:
    - Session loads without crashing.
    - Warning advisory indicates 1 document is unavailable.
    - Active documents list contains Doc A only.
    - Conversation continues seamlessly on remaining available documents.
    """
    headers = {"Authorization": auth_user_a["Authorization"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload Doc A and Doc B
        up_a = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Alpha.pdf", paper_alpha_bytes, "application/pdf")},
            headers=headers,
        )
        doc_a_id = up_a.json()["document_id"]

        up_b = await client.post(
            "/api/documents/upload",
            files={"file": ("Paper_Beta.pdf", paper_beta_bytes, "application/pdf")},
            headers=headers,
        )
        doc_b_id = up_b.json()["document_id"]

        # Create session with both documents
        sess_res = await client.post(
            "/api/chat/sessions",
            json={"title": "Comparative Study Session", "document_ids": [doc_a_id, doc_b_id]},
            headers=headers,
        )
        session_id = sess_res.json()["id"]

        try:
            # Delete Doc B
            del_b = await client.delete(f"/api/documents/{doc_b_id}", headers=headers)
            assert del_b.status_code == 200

            # Reopen session -> must load gracefully without crashing
            reopen_resp = await client.get(f"/api/chat/sessions/{session_id}", headers=headers)
            assert reopen_resp.status_code == 200
            data = reopen_resp.json()

            # Verify unavailable document detection and warning
            assert data["unavailable_documents_count"] >= 1
            assert data["warning_message"] is not None
            assert "no longer available" in data["warning_message"].lower()

            # Active documents must only contain Doc A
            active_doc_ids = [d["id"] for d in data["documents"]]
            assert doc_a_id in active_doc_ids
            assert doc_b_id not in active_doc_ids

            # User can still continue conversation with remaining Doc A
            msg_res = await client.post(
                f"/api/chat/sessions/{session_id}/messages",
                json={"question": "What passage weighting is used in Paper Alpha?"},
                headers=headers,
            )
            assert msg_res.status_code == 200
            assert "bm25" in msg_res.json()["answer"].lower()

        finally:
            await client.delete(f"/api/documents/{doc_a_id}", headers=headers)
            await client.delete(f"/api/chat/sessions/{session_id}", headers=headers)


# =============================================================================
# 6. QUERY REWRITER UNIT TESTS
# =============================================================================

def test_query_rewriter_coreference_and_title():
    """Unit test QueryRewriter coreference detection, contextualization, and title generation."""
    rewriter = QueryRewriter()

    # Coreference detection
    assert rewriter.should_rewrite("What dataset does it use?") is True
    assert rewriter.should_rewrite("Compare the results of the first paper.") is True
    assert rewriter.should_rewrite("What is dense vector retrieval?") is False

    # Title generation
    t1 = rewriter.generate_chat_title("What is the primary methodology used in this research paper?")
    assert "Methodology" in t1
    assert len(t1.split()) <= 8

    t2 = rewriter.generate_chat_title("Compare the datasets used in these papers.")
    assert "Datasets" in t2 or "Compare" in t2
    assert len(t2.split()) <= 8

    # Query rewriting with ordinal document reference
    doc_names = ["Paper_Alpha.pdf", "Paper_Beta.pdf"]
    rewritten = rewriter.rewrite_query_for_retrieval(
        question="What architecture did the first paper use?",
        conversation_history=[
            {"role": "user", "content": "Tell me about the two papers."},
            {"role": "assistant", "content": "Paper Alpha uses inverted index, Paper Beta uses transformers."},
        ],
        document_names=doc_names,
    )
    assert "Paper_Alpha" in rewritten or "Alpha" in rewritten
