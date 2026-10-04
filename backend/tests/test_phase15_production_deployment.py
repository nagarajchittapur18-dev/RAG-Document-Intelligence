import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.document_store import DatabaseManager
from app.services.storage import LocalStorageProvider, S3StorageProvider, get_storage_provider
from app.services.vector_store import VectorStore


@pytest.fixture
def client():
    return TestClient(app)


def test_database_manager_ping_and_health(client):
    """Verifies database ping, deep health check, and Kubernetes probes."""
    db = DatabaseManager()
    assert db.ping() is True

    # Check /api/health
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    data = res_health.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert data["vector_store"] == "healthy"

    # Check /api/health/live
    res_live = client.get("/api/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    # Check /api/health/ready
    res_ready = client.get("/api/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


def test_storage_provider_local_save_read_delete():
    """Verifies LocalStorageProvider save, get_file, get_local_path, and delete operations."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        provider = LocalStorageProvider(upload_dir=tmp_dir)
        test_content = b"%PDF-1.4 test document content for storage verification"
        filename = "test_doc_storage.pdf"

        # 1. Save
        saved_path = provider.save_file(test_content, filename)
        assert os.path.exists(saved_path)
        assert provider.file_exists(saved_path) is True

        # 2. Read
        read_bytes = provider.get_file(saved_path)
        assert read_bytes == test_content

        # 3. Local path access
        local_path = provider.get_local_path(saved_path)
        assert local_path == saved_path

        # 4. Path traversal defense
        with pytest.raises(ValueError, match="Path traversal detected"):
            provider.save_file(test_content, "../../etc/passwd")

        # 5. Delete
        assert provider.delete_file(saved_path) is True
        assert provider.file_exists(saved_path) is False


def test_s3_storage_provider_mock():
    """Verifies S3StorageProvider logic using mocked boto3 client."""
    with tempfile.TemporaryDirectory() as tmp_cache:
        mock_boto = MagicMock()
        mock_s3 = MagicMock()
        mock_boto.client.return_value = mock_s3

        with patch.dict("sys.modules", {"boto3": mock_boto}):
            provider = S3StorageProvider(
                bucket_name="test-docurag-bucket",
                endpoint_url="https://r2.cloudflarestorage.com",
                region_name="us-east-1",
                access_key="mock_key",
                secret_key="mock_secret",
                cache_dir=tmp_cache,
            )

            test_data = b"S3 mock content"
            storage_uri = provider.save_file(test_data, "s3_test.pdf")
            assert storage_uri == "s3://test-docurag-bucket/s3_test.pdf"
            mock_s3.put_object.assert_called_once()

            # Test delete
            assert provider.delete_file("s3_test.pdf") is True
            mock_s3.delete_object.assert_called_once()


def test_chroma_remote_client_configuration():
    """Verifies that setting CHROMA_HOST switches VectorStore to chromadb.HttpClient."""
    with patch("app.services.vector_store.settings.CHROMA_HOST", "chroma.internal.cloud"), \
         patch("app.services.vector_store.settings.CHROMA_PORT", 8000), \
         patch("app.services.vector_store.chromadb.HttpClient") as mock_http_client:
        mock_instance = MagicMock()
        mock_http_client.return_value = mock_instance

        vs = VectorStore()
        mock_http_client.assert_called_once_with(
            host="chroma.internal.cloud",
            port=8000,
            ssl=False,
        )


def test_production_security_headers_and_request_id(client):
    """Verifies that all responses carry production security headers and distributed tracing IDs."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "X-Response-Time-Ms" in res.headers


def test_cors_origin_parsing():
    """Verifies that comma-separated CORS origins are correctly parsed into a list."""
    from app.config import Settings
    custom_settings = Settings(CORS_ORIGINS="https://docurag.vercel.app, https://demo.docurag.io")
    assert "https://docurag.vercel.app" in custom_settings.CORS_ORIGINS
    assert "https://demo.docurag.io" in custom_settings.CORS_ORIGINS
    assert len(custom_settings.CORS_ORIGINS) == 2
