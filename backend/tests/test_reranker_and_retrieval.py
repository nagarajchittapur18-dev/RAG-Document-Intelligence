import io
from unittest.mock import MagicMock, patch
import pytest
import pymupdf
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import SourceCitation
from app.services.reranker import RerankerService
from app.services.retrieval import RetrievalService, is_comparison_query
from app.services.vector_store import SearchResult, VectorStore


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Registers and logs in a test user, returning auth headers."""
    email = "reranker_tester@ragmate.edu"
    client.post("/api/auth/register", json={"name": "Reranker Tester", "email": email, "password": "Password123!"})
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_candidates():
    """Provides sample SearchResult chunks with distinct semantic content."""
    return [
        SearchResult(
            chunk_id="c_unrelated",
            document_id="doc_1",
            document_name="deep_learning.pdf",
            page_number=1,
            text="The history of computer graphics and GPU rendering architectures in the 1990s.",
            similarity_score=0.72,
        ),
        SearchResult(
            chunk_id="c_highly_relevant",
            document_id="doc_1",
            document_name="deep_learning.pdf",
            page_number=3,
            text="We introduce deep residual learning to solve the degradation problem in neural networks with skip connections.",
            similarity_score=0.85,
        ),
        SearchResult(
            chunk_id="c_medium_relevant",
            document_id="doc_1",
            document_name="deep_learning.pdf",
            page_number=5,
            text="Optimization of deep networks suffers when layers increase, leading to convergence difficulties.",
            similarity_score=0.81,
        ),
    ]


def create_test_pdf_stream(pages_content: list[str]) -> io.BytesIO:
    """Creates an in-memory PDF stream for test ingestion."""
    doc = pymupdf.open()
    for text in pages_content:
        page = doc.new_page(width=595, height=842)
        if text:
            page.insert_text((50, 72), text, fontsize=11)
    stream = io.BytesIO(doc.tobytes())
    doc.close()
    stream.seek(0)
    return stream


def test_comparison_intent_detection():
    """Verify deterministic detection of comparison queries without LLM overhead."""
    assert is_comparison_query("Compare the architectures of ResNet and Transformers") is True
    assert is_comparison_query("What is the difference between BERT and GPT?") is True
    assert is_comparison_query("Paper A versus Paper B BLEU score") is True
    assert is_comparison_query("Contrast the optimization techniques used in both papers") is True
    assert is_comparison_query("What dataset was used for training?") is False
    assert is_comparison_query("Explain residual learning with skip connections") is False


def test_reranker_service_direct_ranking(sample_candidates):
    """Verify RerankerService reranks candidates by relevance and attaches rerank_score."""
    reranker = RerankerService()
    query = "What is the degradation problem and how do skip connections solve it?"

    # We mock CrossEncoder.predict to ensure fast, deterministic testing without heavy CPU inference
    # Logits: high for c_highly_relevant, medium for c_medium_relevant, low for c_unrelated
    mock_logits = [-2.5, 4.2, 1.1]

    mock_model = MagicMock()
    mock_model.predict.return_value = mock_logits

    with patch.object(reranker, "_get_model", return_value=mock_model):
        results = reranker.rerank(query=query, candidates=sample_candidates, top_k=2)

        assert len(results) == 2
        # Most relevant chunk should now be ranked #1
        assert results[0].chunk_id == "c_highly_relevant"
        assert results[0].rerank_score is not None
        assert 0.0 <= results[0].rerank_score <= 1.0
        assert results[0].similarity_score == 0.85

        # Second chunk should be medium relevant
        assert results[1].chunk_id == "c_medium_relevant"
        assert results[1].rerank_score < results[0].rerank_score


def test_reranker_disabled_fallback(sample_candidates):
    """Verify that when reranker is disabled, vector similarity order is preserved."""
    reranker = RerankerService()
    with patch.object(reranker, "enabled", False):
        results = reranker.rerank(query="any query", candidates=sample_candidates, top_k=2)

        assert len(results) == 2
        # Sorted strictly by similarity_score descending: 0.85, then 0.81
        assert results[0].chunk_id == "c_highly_relevant"
        assert results[1].chunk_id == "c_medium_relevant"


def test_reranker_exception_fallback(sample_candidates):
    """Verify that if cross-encoder raises an exception, the pipeline gracefully falls back to vector similarity."""
    reranker = RerankerService()
    mock_model = MagicMock()
    mock_model.predict.side_effect = RuntimeError("CUDA/CPU tensor allocation failure")

    with patch.object(reranker, "_get_model", return_value=mock_model):
        results = reranker.rerank(query="any query", candidates=sample_candidates, top_k=3)

        assert len(results) == 3
        # Should gracefully return vector similarity ordering
        assert results[0].similarity_score >= results[1].similarity_score >= results[2].similarity_score


def test_retrieval_service_with_reranker_orchestration():
    """Verify RetrievalService coordinates candidate vector search and reranking."""
    mock_vector_store = MagicMock(spec=VectorStore)
    mock_vector_store.similarity_search.return_value = [
        SearchResult(
            chunk_id=f"chunk_{i}",
            document_id="doc_1",
            document_name="test.pdf",
            page_number=i,
            text=f"Text excerpt {i}",
            similarity_score=0.70 + (i * 0.02),
        )
        for i in range(10)
    ]

    mock_reranker = MagicMock(spec=RerankerService)
    mock_reranker.enabled = True
    # Reranker reverses the order (favoring chunk_0)
    def fake_rerank(query, candidates, top_k=None):
        for idx, c in enumerate(candidates):
            c.rerank_score = 0.99 - (idx * 0.05)
        candidates.sort(key=lambda x: x.rerank_score, reverse=True)
        return candidates[:top_k] if top_k else candidates

    mock_reranker.rerank.side_effect = fake_rerank

    service = RetrievalService(vector_store=mock_vector_store, reranker=mock_reranker)
    final_chunks = service.retrieve(
        query="What is the architecture?",
        top_k=3,
        document_ids=["doc_1"],
        user_id="user_123",
        enable_reranking=True,
    )

    assert len(final_chunks) == 3
    assert final_chunks[0].chunk_id == "chunk_0"
    assert final_chunks[0].rerank_score == 0.99
    assert mock_vector_store.similarity_search.called
    assert mock_reranker.rerank.called


def test_comparison_query_balancing_across_documents():
    """Verify that comparison queries balance chunks across multiple documents."""
    mock_vector_store = MagicMock(spec=VectorStore)
    # 6 chunks from Paper A, 4 chunks from Paper B
    mock_vector_store.similarity_search.return_value = [
        SearchResult(chunk_id=f"a_{i}", document_id="doc_a", document_name="PaperA.pdf", page_number=1, text=f"Paper A text {i}", similarity_score=0.90 - (i * 0.02))
        for i in range(6)
    ] + [
        SearchResult(chunk_id=f"b_{i}", document_id="doc_b", document_name="PaperB.pdf", page_number=1, text=f"Paper B text {i}", similarity_score=0.85 - (i * 0.02))
        for i in range(4)
    ]

    # Without balancing, Paper A would take all top 4 slots (0.90, 0.88, 0.86, 0.84)
    # With comparison query and balancing, both Paper A and Paper B must be represented
    service = RetrievalService(vector_store=mock_vector_store)
    with patch.object(service.reranker, "enabled", False):
        balanced_chunks = service.retrieve(
            query="Compare the methodologies of Paper A and Paper B",
            top_k=4,
            document_ids=["doc_a", "doc_b"],
            user_id="user_test",
        )

        assert len(balanced_chunks) == 4
        doc_ids_present = {c.document_id for c in balanced_chunks}
        assert "doc_a" in doc_ids_present
        assert "doc_b" in doc_ids_present


def test_retrieval_compare_endpoint(client, auth_headers):
    """Verify POST /api/evaluation/retrieval-compare returns dual rankings and latency benchmarks."""
    # 1. Upload a test PDF
    pdf_stream = create_test_pdf_stream([
        "Page 1: Benchmark evaluation of dense semantic vector retrieval against cross-encoder rerankers.",
        "Page 2: Experimental results show MRR@10 and NDCG improvements with two-stage pipeline.",
    ])
    up_res = client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("retrieval_eval.pdf", pdf_stream, "application/pdf")},
    )
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    # 2. Call comparison endpoint
    compare_res = client.post(
        "/api/evaluation/retrieval-compare",
        headers=auth_headers,
        json={
            "question": "What are the experimental results for MRR?",
            "document_ids": [doc_id],
            "candidate_k": 10,
            "final_k": 3,
        },
    )
    assert compare_res.status_code == 200
    data = compare_res.json()

    assert data["question"] == "What are the experimental results for MRR?"
    assert data["candidate_count"] > 0
    assert len(data["vector_only_chunks"]) > 0
    assert len(data["reranked_chunks"]) > 0
    assert data["vector_latency_ms"] >= 0
    assert data["rerank_latency_ms"] >= 0
    assert data["total_latency_ms"] >= data["vector_latency_ms"]


def test_end_to_end_chat_citations_with_rerank_scores(client, auth_headers):
    """Verify chat endpoint preserves both retrieval_score and rerank_score in citations."""
    # 1. Upload document
    pdf_stream = create_test_pdf_stream([
        "Page 1: DocuRAG two-stage retrieval enhances precision using cross-encoder reranking.",
    ])
    up_res = client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("two_stage_paper.pdf", pdf_stream, "application/pdf")},
    )
    doc_id = up_res.json()["document_id"]

    # 2. Create session and ask question
    sess_res = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={"title": "Reranker Test Session", "document_ids": [doc_id]},
    )
    session_id = sess_res.json()["id"]

    mock_answer = "DocuRAG uses cross-encoder reranking to enhance retrieval precision [1]."
    with patch("app.api.chat.gemini_service._call_gemini_api", return_value=mock_answer):
        ask_res = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            headers=auth_headers,
            json={"question": "How does DocuRAG enhance precision?"},
        )
        assert ask_res.status_code == 200
        sources = ask_res.json()["sources"]
        assert len(sources) > 0
        first = sources[0]
        assert first["citation_id"] == 1
        assert "retrieval_score" in first
        assert "relevance_score" in first
        assert first["document_name"] == "two_stage_paper.pdf"

    # 3. Reload session and verify scores persisted in SQLite
    get_sess = client.get(f"/api/chat/sessions/{session_id}", headers=auth_headers)
    assert get_sess.status_code == 200
    msgs = get_sess.json()["messages"]
    assistant_msg = next(m for m in msgs if m["role"] == "assistant")
    saved_sources = assistant_msg["sources"]
    assert len(saved_sources) > 0
    assert "retrieval_score" in saved_sources[0]
