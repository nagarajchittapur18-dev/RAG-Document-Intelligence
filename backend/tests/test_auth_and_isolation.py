import uuid
import pytest
from httpx import ASGITransport, AsyncClient
import pymupdf

from app.main import app
from app.services.gemini import SAFE_FALLBACK_ANSWER


def create_test_pdf(text: str) -> bytes:
    """Helper creating a 1-page PDF with custom text."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_register_and_validation():
    """Verify user registration and input validations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_suffix = uuid.uuid4().hex[:6]
        valid_email = f"user_{unique_suffix}@example.com"

        # 1. Valid registration
        res = await client.post(
            "/api/auth/register",
            json={
                "name": "Alice Researcher",
                "email": valid_email,
                "password": "SecurePassword123",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["user"]["email"] == valid_email
        assert data["user"]["name"] == "Alice Researcher"
        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]

        # 2. Duplicate email rejection
        res_dup = await client.post(
            "/api/auth/register",
            json={
                "name": "Alice Duplicate",
                "email": valid_email,
                "password": "SecurePassword123",
            },
        )
        assert res_dup.status_code == 409
        assert "already registered" in res_dup.json()["detail"].lower()

        # 3. Empty name validation
        res_bad_name = await client.post(
            "/api/auth/register",
            json={
                "name": "   ",
                "email": f"other_{unique_suffix}@example.com",
                "password": "SecurePassword123",
            },
        )
        assert res_bad_name.status_code == 422 or res_bad_name.status_code == 400

        # 4. Short password validation
        res_bad_pwd = await client.post(
            "/api/auth/register",
            json={
                "name": "Bob",
                "email": f"bob_{unique_suffix}@example.com",
                "password": "short",
            },
        )
        assert res_bad_pwd.status_code == 422 or res_bad_pwd.status_code == 400


@pytest.mark.asyncio
async def test_login_and_token_flow():
    """Verify user login and JWT bearer token issuance."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_suffix = uuid.uuid4().hex[:6]
        email = f"logintest_{unique_suffix}@example.com"
        password = "MyStrongPassword2026!"

        # Register user
        reg_res = await client.post(
            "/api/auth/register",
            json={"name": "Login Tester", "email": email, "password": password},
        )
        assert reg_res.status_code == 201

        # 1. Login with correct credentials
        login_res = await client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert "access_token" in login_data
        assert login_data["token_type"] == "bearer"
        assert login_data["expires_in"] > 0
        assert login_data["user"]["email"] == email

        token = login_data["access_token"]
        auth_header = {"Authorization": f"Bearer {token}"}

        # 2. Access /api/auth/me with valid token
        me_res = await client.get("/api/auth/me", headers=auth_header)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == email

        # 3. Access /api/auth/me without token -> 401
        unauth_res = await client.get("/api/auth/me")
        assert unauth_res.status_code == 401

        # 4. Access /api/auth/me with bogus token -> 401
        bogus_res = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert bogus_res.status_code == 401

        # 5. Login with invalid password -> 401
        bad_login = await client.post(
            "/api/auth/login",
            json={"email": email, "password": "WrongPassword!"},
        )
        assert bad_login.status_code == 401

        # 6. Login with unknown email -> 401
        unknown_login = await client.post(
            "/api/auth/login",
            json={"email": "nobody@nowhere.com", "password": password},
        )
        assert unknown_login.status_code == 401


@pytest.mark.asyncio
async def test_multi_tenant_document_and_vector_isolation():
    """
    CRITICAL MULTI-TENANT TEST:
    Verify User A and User B cannot access, list, query, or delete each other's documents or ChromaDB vector chunks.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create User A
        suffix_a = uuid.uuid4().hex[:6]
        email_a = f"usera_{suffix_a}@example.com"
        await client.post("/api/auth/register", json={"name": "User A", "email": email_a, "password": "PasswordA123"})
        login_a = await client.post("/api/auth/login", json={"email": email_a, "password": "PasswordA123"})
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Create User B
        suffix_b = uuid.uuid4().hex[:6]
        email_b = f"userb_{suffix_b}@example.com"
        await client.post("/api/auth/register", json={"name": "User B", "email": email_b, "password": "PasswordB123"})
        login_b = await client.post("/api/auth/login", json={"email": email_b, "password": "PasswordB123"})
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 1. User A uploads a confidential document
        secret_content = (
            "CONFIDENTIAL DOCUMENT FOR USER A ONLY\n"
            "The Project Pegasus secret access code is Delta-99-Quantum.\n"
            "All unauthorized access will be audited immediately."
        )
        pdf_bytes_a = create_test_pdf(secret_content)
        upload_a = await client.post(
            "/api/documents/upload",
            files={"file": ("pegasus_secret.pdf", pdf_bytes_a, "application/pdf")},
            headers=headers_a,
        )
        assert upload_a.status_code == 201
        doc_id_a = upload_a.json()["document_id"]

        # 2. User B uploads a different document
        public_content = (
            "GENERAL KNOWLEDGE REPORT\n"
            "Photosynthesis is the process by which green plants make food using sunlight and water."
        )
        pdf_bytes_b = create_test_pdf(public_content)
        upload_b = await client.post(
            "/api/documents/upload",
            files={"file": ("photosynthesis.pdf", pdf_bytes_b, "application/pdf")},
            headers=headers_b,
        )
        assert upload_b.status_code == 201
        doc_id_b = upload_b.json()["document_id"]

        try:
            # 3. Document Listing Isolation:
            # User A's list must contain doc_id_a and NOT doc_id_b
            list_a = await client.get("/api/documents", headers=headers_a)
            assert list_a.status_code == 200
            docs_a = [d["id"] for d in list_a.json()["documents"]]
            assert doc_id_a in docs_a
            assert doc_id_b not in docs_a

            # User B's list must contain doc_id_b and NOT doc_id_a
            list_b = await client.get("/api/documents", headers=headers_b)
            assert list_b.status_code == 200
            docs_b = [d["id"] for d in list_b.json()["documents"]]
            assert doc_id_b in docs_b
            assert doc_id_a not in docs_b

            # 4. Cross-Tenant Document Access Rejection:
            # User B cannot access User A's document details -> 404
            get_foreign = await client.get(f"/api/documents/{doc_id_a}", headers=headers_b)
            assert get_foreign.status_code == 404

            # User B cannot delete User A's document -> 404
            del_foreign = await client.delete(f"/api/documents/{doc_id_a}", headers=headers_b)
            assert del_foreign.status_code == 404

            # 5. Cross-Tenant Explicit Scoping Rejection:
            # If User B tries to query User A's document by specifying document_ids=[doc_id_a] -> 404
            cross_scope_qa = await client.post(
                "/api/chat/ask",
                json={
                    "question": "What is the Project Pegasus secret access code?",
                    "document_ids": [doc_id_a],
                },
                headers=headers_b,
            )
            assert cross_scope_qa.status_code == 404

            # 6. ChromaDB Vector Isolation:
            # When User B asks about Project Pegasus across ALL their documents (no document_ids passed),
            # ChromaDB must filter chunks to User B, so User A's chunks are never retrieved.
            unscoped_qa = await client.post(
                "/api/chat/ask",
                json={
                    "question": "What is the Project Pegasus secret access code?",
                },
                headers=headers_b,
            )
            assert unscoped_qa.status_code == 200
            qa_res_b = unscoped_qa.json()
            assert SAFE_FALLBACK_ANSWER in qa_res_b["answer"]
            assert qa_res_b["retrieved_chunks"] == 0

        finally:
            # Clean up documents
            await client.delete(f"/api/documents/{doc_id_a}", headers=headers_a)
            await client.delete(f"/api/documents/{doc_id_b}", headers=headers_b)


@pytest.mark.asyncio
async def test_chat_sessions_multi_tenant_isolation():
    """Verify chat sessions are strictly private to each user."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create User A & User B
        suffix = uuid.uuid4().hex[:6]
        await client.post("/api/auth/register", json={"name": "Alice", "email": f"a_{suffix}@ex.com", "password": "Password123"})
        await client.post("/api/auth/register", json={"name": "Bob", "email": f"b_{suffix}@ex.com", "password": "Password123"})

        login_a = await client.post("/api/auth/login", json={"email": f"a_{suffix}@ex.com", "password": "Password123"})
        login_b = await client.post("/api/auth/login", json={"email": f"b_{suffix}@ex.com", "password": "Password123"})

        headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        # 1. User A creates chat session
        session_res = await client.post(
            "/api/chat/sessions",
            json={"title": "Alice Private Session"},
            headers=headers_a,
        )
        assert session_res.status_code == 201
        session_id = session_res.json()["id"]

        # 2. User B cannot see Alice's session in their list
        list_b = await client.get("/api/chat/sessions", headers=headers_b)
        assert list_b.status_code == 200
        b_session_ids = [s["id"] for s in list_b.json()["sessions"]]
        assert session_id not in b_session_ids

        # 3. User B cannot view Alice's session -> 404
        get_b = await client.get(f"/api/chat/sessions/{session_id}", headers=headers_b)
        assert get_b.status_code == 404

        # 4. User B cannot delete Alice's session -> 404
        del_b = await client.delete(f"/api/chat/sessions/{session_id}", headers=headers_b)
        assert del_b.status_code == 404

        # 5. Alice can view and delete her own session
        get_a = await client.get(f"/api/chat/sessions/{session_id}", headers=headers_a)
        assert get_a.status_code == 200
        assert get_a.json()["session"]["title"] == "Alice Private Session"

        del_a = await client.delete(f"/api/chat/sessions/{session_id}", headers=headers_a)
        assert del_a.status_code == 200
