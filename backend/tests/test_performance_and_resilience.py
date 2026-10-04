"""
Phase 14 Performance, Resilience, Singletons, and Health Check Test Suite.
Tests:
- Singleton model loading (EmbeddingService, RerankerService)
- Batch embedding performance and normalization
- Reranker graceful fallback on error or disablement
- System health, liveness, and readiness probes
- In-memory rate limiting and HTTP 429 enforcement
- Multi-page PDF extraction and chunking performance benchmarking
"""

import time
import pytest
import numpy as np
from fastapi import HTTPException
from fastapi.testclient import TestClient
import pymupdf

from app.main import app
from app.services.embedding_service import EmbeddingService
from app.services.reranker import RerankerService
from app.services.vector_store import SearchResult
from app.services.pdf_processor import PDFProcessor
from app.services.chunker import DocumentChunker
from app.utils.rate_limiter import InMemoryRateLimiter

client = TestClient(app)


# =============================================================================
# 1. MODEL LOADING SINGLETON VERIFICATION
# =============================================================================

def test_embedding_service_singleton():
    service1 = EmbeddingService()
    service2 = EmbeddingService()
    assert service1 is service2
    assert service1.model is service2.model


def test_reranker_service_singleton():
    reranker1 = RerankerService()
    reranker2 = RerankerService()
    assert reranker1 is reranker2


# =============================================================================
# 2. BATCH EMBEDDING PERFORMANCE & NORMALIZATION
# =============================================================================

def test_batch_embedding_behavior_and_normalization():
    service = EmbeddingService()

    # Empty batch
    assert service.embed_texts([]) == []

    # Multi-text batch
    texts = [
        "Dense vector retrieval using dual encoders.",
        "Cross-encoders compute joint cross-attention weights.",
        "Retrieval augmented generation reduces hallucinations.",
    ]
    t0 = time.perf_counter()
    embeddings = service.embed_texts(texts, batch_size=3)
    duration_ms = (time.perf_counter() - t0) * 1000

    assert len(embeddings) == 3
    assert duration_ms < 2000  # Batch inference should be very fast for 3 short texts

    for emb in embeddings:
        assert len(emb) == 384
        # Verify L2 normalization: sum(x_i^2) ~= 1.0
        norm = np.linalg.norm(emb)
        assert pytest.approx(norm, abs=1e-3) == 1.0


# =============================================================================
# 3. RERANKER FALLBACK RESILIENCE
# =============================================================================

def test_reranker_disabled_fallback():
    # If disabled, must return candidates sorted by similarity score
    reranker = RerankerService()
    original_enabled = reranker.enabled
    try:
        reranker.enabled = False
        candidates = [
            SearchResult(
                chunk_id="c1", document_id="d1", document_name="d1.pdf",
                page_number=1, text="Text 1", similarity_score=0.45
            ),
            SearchResult(
                chunk_id="c2", document_id="d1", document_name="d1.pdf",
                page_number=2, text="Text 2", similarity_score=0.85
            ),
        ]
        result = reranker.rerank("Query", candidates, top_k=2)
        assert len(result) == 2
        assert result[0].chunk_id == "c2"  # Higher similarity first
        assert result[1].chunk_id == "c1"
    finally:
        reranker.enabled = original_enabled


def test_reranker_error_graceful_fallback(monkeypatch):
    reranker = RerankerService()
    original_enabled = reranker.enabled
    reranker.enabled = True

    # Simulate model prediction error
    def mock_predict(*args, **kwargs):
        raise RuntimeError("GPU/CPU memory fault during prediction")

    class MockModel:
        predict = staticmethod(mock_predict)

    monkeypatch.setattr(reranker, "_get_model", lambda: MockModel())

    candidates = [
        SearchResult(
            chunk_id="c1", document_id="d1", document_name="d1.pdf",
            page_number=1, text="Text 1", similarity_score=0.30
        ),
        SearchResult(
            chunk_id="c2", document_id="d1", document_name="d1.pdf",
            page_number=2, text="Text 2", similarity_score=0.75
        ),
    ]

    # Must not raise an exception, but fall back to similarity ranking
    fallback_res = reranker.rerank("Query", candidates, top_k=2)
    assert len(fallback_res) == 2
    assert fallback_res[0].chunk_id == "c2"
    reranker.enabled = original_enabled


# =============================================================================
# 4. HEALTH, LIVENESS & READINESS PROBES
# =============================================================================

def test_health_check_deep_probe():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ok", "healthy", "degraded")
    assert data["database"] == "healthy"
    assert data["vector_store"] == "healthy"
    assert "environment" in data
    assert data["environment"]["embedding_model"] == "all-MiniLM-L6-v2"


def test_liveness_probe():
    res = client.get("/api/health/live")
    assert res.status_code == 200
    assert res.json()["status"] == "alive"


def test_readiness_probe():
    res = client.get("/api/health/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"


# =============================================================================
# 5. RATE LIMITER FUNCTIONALITY
# =============================================================================

def test_rate_limiter_enforcement():
    limiter = InMemoryRateLimiter(requests_per_minute=3)
    dummy_req = type("DummyRequest", (), {"client": type("Client", (), {"host": "192.168.1.100"})()})()

    # First 3 requests succeed
    limiter.check(dummy_req)
    limiter.check(dummy_req)
    limiter.check(dummy_req)

    # 4th request must raise 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check(dummy_req)
    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers


# =============================================================================
# 6. MULTI-PAGE PDF EXTRACTION & CHUNKING BENCHMARK
# =============================================================================

def test_multi_page_pdf_processing_performance(tmp_path):
    # Generate a synthetic 10-page academic paper PDF
    doc = pymupdf.open()
    for p in range(10):
        page = doc.new_page()
        page.insert_text((50, 72), f"Page {p+1} Header\n\n" + ("Dense retrieval in RAG systems. " * 50))
    pdf_path = tmp_path / "academic_10_pages.pdf"
    doc.save(str(pdf_path))
    doc.close()

    processor = PDFProcessor()
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)

    # Measure extraction time
    t0 = time.perf_counter()
    extracted = processor.extract_document(str(pdf_path))
    extraction_time_s = time.perf_counter() - t0

    assert extracted.page_count == 10
    assert extraction_time_s < 1.0  # 10 pages with PyMuPDF extracts in < 1 second

    # Measure chunking time
    t1 = time.perf_counter()
    chunks = chunker.chunk_document(extracted, document_id="benchmark_doc_10p")
    chunking_time_s = time.perf_counter() - t1

    assert len(chunks) >= 10
    assert chunking_time_s < 0.5
