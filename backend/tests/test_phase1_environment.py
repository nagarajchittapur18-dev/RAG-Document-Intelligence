import os
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from app.config import settings
from app.main import app


def test_directory_structure():
    """Verify that all mandatory project directories exist."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    
    expected_dirs = [
        base_dir / "backend" / "app" / "api",
        base_dir / "backend" / "app" / "models",
        base_dir / "backend" / "app" / "services",
        base_dir / "backend" / "app" / "database",
        base_dir / "backend" / "app" / "utils",
        base_dir / "backend" / "uploads",
        base_dir / "backend" / "chroma_data",
        base_dir / "frontend" / "src" / "components",
        base_dir / "frontend" / "src" / "pages",
        base_dir / "frontend" / "src" / "services",
        base_dir / "evaluation" / "results",
        base_dir / "docs",
        base_dir / "sample_documents",
    ]
    
    for directory in expected_dirs:
        assert directory.exists(), f"Missing required directory: {directory}"
        assert directory.is_dir(), f"Path is not a directory: {directory}"


def test_configuration_loading():
    """Verify that environment settings load with sensible defaults."""
    assert settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2"
    assert settings.CHROMA_PERSIST_DIRECTORY == "./chroma_data"
    assert settings.TOP_K == 5
    assert settings.CHUNK_SIZE == 1000
    assert settings.CHUNK_OVERLAP == 150
    assert len(settings.CORS_ORIGINS) > 0


def test_core_dependencies_importable():
    """Verify that all core RAG and academic evaluation dependencies are importable."""
    import pymupdf
    import chromadb
    import sentence_transformers
    import google.genai
    import google.generativeai
    import sqlalchemy
    import aiosqlite
    import sklearn
    import rank_bm25
    
    assert pymupdf is not None
    assert chromadb is not None
    assert sentence_transformers is not None
    assert google.genai is not None


@pytest.mark.asyncio
async def test_fastapi_health_endpoint():
    """Verify FastAPI application and /api/health endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["environment"]["embedding_model"] == "all-MiniLM-L6-v2"
        assert data["environment"]["vector_store"] == "ChromaDB"


@pytest.mark.asyncio
async def test_fastapi_root_endpoint():
    """Verify FastAPI root status endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["project"] == "RAGMate"
        assert data["status"] == "operational"
