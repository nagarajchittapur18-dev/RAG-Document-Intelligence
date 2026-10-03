import os
from unittest.mock import MagicMock, patch
import pytest
from app.config import settings
from app.services.gemini import (
    GeminiService,
    CitationSource,
    RAGResponse,
    SAFE_FALLBACK_ANSWER,
)
from app.services.vector_store import SearchResult


@pytest.fixture
def sample_search_results():
    return [
        SearchResult(
            chunk_id="doc_12_p2_c0",
            document_id="12",
            document_name="deep_residual_learning.pdf",
            page_number=2,
            text=(
                "When deeper networks are able to start converging, an unexpected degradation problem has been exposed: "
                "with the network depth increasing, accuracy gets saturated (which might be unsurprising) and then "
                "degrades rapidly. Unexpectedly, such degradation is not caused by overfitting, and adding more layers "
                "to a suitably deep model leads to higher training error."
            ),
            similarity_score=0.892,
            metadata={"document_id": "12", "page_number": 2},
        ),
        SearchResult(
            chunk_id="doc_12_p3_c1",
            document_id="12",
            document_name="deep_residual_learning.pdf",
            page_number=3,
            text=(
                "We address the degradation problem by introducing a deep residual learning framework. Instead of hoping "
                "each few stacked layers directly fit a desired underlying mapping, we explicitly let these layers "
                "fit a residual mapping F(x) := H(x) - x."
            ),
            similarity_score=0.841,
            metadata={"document_id": "12", "page_number": 3},
        ),
    ]


def test_no_context_safe_fallback():
    """Verify that empty context returns safe fallback without API calls."""
    service = GeminiService(api_key="fake_key")
    response = service.generate_grounded_answer(
        question="What is the degradation problem?",
        contexts=[],
    )

    assert response.is_grounded is False
    assert response.answer == SAFE_FALLBACK_ANSWER
    assert len(response.sources) == 0
    assert response.retrieval_count == 0
    assert response.model_used == "hallucination_guard"


def test_context_block_construction(sample_search_results):
    """Verify that context blocks preserve document names and page numbers."""
    service = GeminiService(api_key="fake_key")
    block = service.construct_context_block(sample_search_results)

    assert "deep_residual_learning.pdf" in block
    assert "Page 2" in block
    assert "Page 3" in block
    assert "doc_12_p2_c0" in block
    assert "degradation problem" in block


def test_missing_api_key_returns_advisory(sample_search_results):
    """Verify clean advisory when no API key is configured."""
    service = GeminiService(api_key="")
    response = service.generate_grounded_answer(
        question="What is residual learning?",
        contexts=sample_search_results,
    )

    assert response.is_grounded is False
    assert "GEMINI_API_KEY is not configured" in response.answer
    assert len(response.sources) == 2


def test_grounded_answer_with_mocked_gemini(sample_search_results):
    """Verify answer generation and source citation binding with mock."""
    service = GeminiService(api_key="mock_key")
    
    # Mock API call
    expected_answer = (
        "The degradation problem occurs when increasing network depth leads to accuracy saturation "
        "and higher training error, which is not caused by overfitting."
    )
    with patch.object(service, "_call_gemini_api", return_value=expected_answer):
        response = service.generate_grounded_answer(
            question="What is the degradation problem?",
            contexts=sample_search_results,
        )

        assert response.is_grounded is True
        assert response.answer == expected_answer
        assert len(response.sources) == 2
        assert response.sources[0].document_name == "deep_residual_learning.pdf"
        assert response.sources[0].page_number == 2
        assert response.sources[0].chunk_id == "doc_12_p2_c0"
        assert response.sources[1].page_number == 3


def test_unanswerable_question_fallback_with_mock(sample_search_results):
    """Verify that when context does not contain answer, fallback is recognized."""
    service = GeminiService(api_key="mock_key")
    
    with patch.object(service, "_call_gemini_api", return_value=SAFE_FALLBACK_ANSWER):
        response = service.generate_grounded_answer(
            question="What is the recipe for baking chocolate brownies?",
            contexts=sample_search_results,
        )

        assert response.is_grounded is False
        assert SAFE_FALLBACK_ANSWER in response.answer
        assert len(response.sources) == 0


@pytest.mark.skipif(
    not settings.GEMINI_API_KEY,
    reason="GEMINI_API_KEY not configured for live integration test",
)
def test_live_gemini_grounded_qa(sample_search_results):
    """Live integration test against Google Gemini API verifying grounded answering."""
    service = GeminiService()
    response = service.generate_grounded_answer(
        question="According to the document, what causes the degradation problem?",
        contexts=sample_search_results,
    )

    assert response.is_grounded is True
    assert len(response.answer) > 20
    # ResNet text specifically states degradation is NOT caused by overfitting
    assert "overfitting" in response.answer.lower()
    assert len(response.sources) == 2
    assert response.sources[0].page_number in [2, 3]
    assert response.latency_ms > 0
