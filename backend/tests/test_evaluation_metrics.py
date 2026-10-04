"""
Unit tests for Information Retrieval (IR) metric functions and error classifiers.
Verifies mathematical precision, edge case safety, zero-division handling, and deduplication.
"""

import pytest
from app.services.evaluation_engine import (
    calculate_improvement_percentage,
    classify_evaluation_error,
    compute_abstention_accuracy,
    compute_document_hit_rate_at_k,
    compute_hit_rate_at_k,
    compute_page_hit_rate_at_k,
    compute_precision_at_k,
    compute_recall_at_k,
    compute_reciprocal_rank,
    compute_statistical_summary,
    deduplicate_list,
)


def test_deduplicate_list():
    assert deduplicate_list(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
    assert deduplicate_list([]) == []
    assert deduplicate_list([1, 2, 3]) == [1, 2, 3]


def test_precision_at_k_standard_and_edge_cases():
    retrieved = ["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5"]
    expected = ["chunk_2", "chunk_5"]

    # At K=1: chunk_1 is not relevant -> 0/1 = 0.0
    assert compute_precision_at_k(retrieved, expected, k=1) == 0.0

    # At K=2: chunk_2 is relevant -> 1/2 = 0.5
    assert compute_precision_at_k(retrieved, expected, k=2) == 0.5

    # At K=5: chunk_2 and chunk_5 are relevant -> 2/5 = 0.4
    assert compute_precision_at_k(retrieved, expected, k=5) == 0.4

    # Edge cases
    assert compute_precision_at_k(retrieved, expected, k=0) == 0.0
    assert compute_precision_at_k(retrieved, expected, k=-5) == 0.0
    assert compute_precision_at_k([], expected, k=5) == 0.0
    assert compute_precision_at_k(retrieved, [], k=5) == 0.0


def test_precision_duplicate_handling_prevents_inflation():
    # If duplicates were not deduplicated, chunk_1 repeated 5 times would falsely claim 5/5 = 1.0
    retrieved_with_dups = ["chunk_1", "chunk_1", "chunk_1", "chunk_2", "chunk_3"]
    expected = ["chunk_1"]
    # Top 3 unique chunks: ["chunk_1", "chunk_2", "chunk_3"] -> 1 hit out of 3 = 0.3333
    assert compute_precision_at_k(retrieved_with_dups, expected, k=3) == pytest.approx(0.3333, 0.001)


def test_recall_at_k():
    retrieved = ["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5"]
    expected = ["chunk_2", "chunk_5", "chunk_8", "chunk_9"]  # 4 expected items

    # At K=2: only chunk_2 found -> 1/4 = 0.25
    assert compute_recall_at_k(retrieved, expected, k=2) == 0.25

    # At K=5: chunk_2 and chunk_5 found -> 2/4 = 0.50
    assert compute_recall_at_k(retrieved, expected, k=5) == 0.50

    # If all expected retrieved:
    all_retrieved = ["chunk_2", "chunk_5", "chunk_8", "chunk_9"]
    assert compute_recall_at_k(all_retrieved, expected, k=5) == 1.0

    # Edge cases
    assert compute_recall_at_k([], expected, k=5) == 0.0
    assert compute_recall_at_k(retrieved, [], k=5) == 0.0


def test_hit_rate_at_k():
    retrieved = ["chunk_1", "chunk_2", "chunk_3"]
    expected = ["chunk_2"]

    assert compute_hit_rate_at_k(retrieved, expected, k=1) == 0.0
    assert compute_hit_rate_at_k(retrieved, expected, k=2) == 1.0
    assert compute_hit_rate_at_k(retrieved, expected, k=5) == 1.0

    assert compute_hit_rate_at_k([], expected, k=3) == 0.0
    assert compute_hit_rate_at_k(retrieved, [], k=3) == 0.0


def test_reciprocal_rank_calculation():
    # Rank 1 hit: RR = 1/1 = 1.0
    assert compute_reciprocal_rank(["c1", "c2", "c3"], ["c1"]) == 1.0

    # Rank 2 hit: RR = 1/2 = 0.5
    assert compute_reciprocal_rank(["c1", "c2", "c3"], ["c2"]) == 0.5

    # Rank 4 hit: RR = 1/4 = 0.25
    assert compute_reciprocal_rank(["c1", "c2", "c3", "c4"], ["c4"]) == 0.25

    # Not found in candidate set
    assert compute_reciprocal_rank(["c1", "c2", "c3"], ["c99"]) == 0.0
    assert compute_reciprocal_rank([], ["c1"]) == 0.0
    assert compute_reciprocal_rank(["c1"], []) == 0.0


def test_page_and_document_hit_rate():
    retrieved_pages = [1, 2, 5, 8]
    assert compute_page_hit_rate_at_k(retrieved_pages, [5], k=2) == 0.0
    assert compute_page_hit_rate_at_k(retrieved_pages, [5], k=3) == 1.0
    assert compute_page_hit_rate_at_k(retrieved_pages, [], k=3) == 0.0

    retrieved_docs = ["docA", "docB", "docC"]
    assert compute_document_hit_rate_at_k(retrieved_docs, ["docB"], k=1) == 0.0
    assert compute_document_hit_rate_at_k(retrieved_docs, ["docB"], k=2) == 1.0
    assert compute_document_hit_rate_at_k(retrieved_docs, [], k=2) == 0.0


def test_abstention_accuracy():
    # Unanswerable with explicit refusal marker -> 1.0
    refusal_ans = "I could not find sufficient information in the selected documents to answer this question."
    assert compute_abstention_accuracy(is_unanswerable=True, answer_text=refusal_ans) == 1.0

    # Unanswerable with low candidate similarity (< 0.15) -> 1.0
    assert compute_abstention_accuracy(is_unanswerable=True, candidate_max_similarity=0.08) == 1.0

    # Unanswerable but generated fabricated text without refusal -> 0.0
    hallucinated_ans = "Google earned 45 billion dollars in 2024 with a margin of 28%."
    assert compute_abstention_accuracy(is_unanswerable=True, answer_text=hallucinated_ans) == 0.0

    # Answerable question with valid factual response -> 1.0
    valid_ans = "The model produces 384-dimensional embeddings."
    assert compute_abstention_accuracy(is_unanswerable=False, answer_text=valid_ans) == 1.0

    # Answerable question with false refusal -> 0.0
    assert compute_abstention_accuracy(is_unanswerable=False, answer_text=refusal_ans) == 0.0


def test_improvement_percentage_calculation():
    # Regular positive gain: (0.90 - 0.75) / 0.75 = +20.0%
    assert calculate_improvement_percentage(0.75, 0.90) == 20.0

    # Regular negative decrease: (0.70 - 0.80) / 0.80 = -12.5%
    assert calculate_improvement_percentage(0.80, 0.70) == -12.5

    # Identical: 0.0%
    assert calculate_improvement_percentage(0.85, 0.85) == 0.0

    # Zero baseline handling
    assert calculate_improvement_percentage(0.0, 0.50) == 100.0
    assert calculate_improvement_percentage(0.0, 0.0) == 0.0


def test_statistical_summary_calculator():
    # Empty list
    empty_stats = compute_statistical_summary([])
    assert empty_stats["mean"] == 0.0
    assert empty_stats["std_dev"] == 0.0

    # Single item
    single_stats = compute_statistical_summary([42.0])
    assert single_stats["mean"] == 42.0
    assert single_stats["median"] == 42.0
    assert single_stats["std_dev"] == 0.0

    # Known distribution: [10, 20, 30, 40, 50]
    # Mean: 30, Median: 30, Min: 10, Max: 50, Sample StDev = sqrt(250) ≈ 15.8114
    stats = compute_statistical_summary([10.0, 20.0, 30.0, 40.0, 50.0])
    assert stats["mean"] == 30.0
    assert stats["median"] == 30.0
    assert stats["min"] == 10.0
    assert stats["max"] == 50.0
    assert stats["std_dev"] == pytest.approx(15.8114, 0.001)


def test_classify_evaluation_error_outcomes():
    # 1. Unanswerable success
    res_unans = classify_evaluation_error(
        is_unanswerable=True,
        expected_chunk_ids=[],
        all_candidates=["c1", "c2"],
        vector_top_k=["c1"],
        reranked_top_k=["c1"],
        expected_pages=[],
        retrieved_pages=[1],
        max_relevance_score=0.02,
        abstention_threshold=0.15,
    )
    assert res_unans == "unanswerable_abstention_success"

    # 2. Success (target chunk in top-5 reranked)
    res_success = classify_evaluation_error(
        is_unanswerable=False,
        expected_chunk_ids=["target_c"],
        all_candidates=["c1", "target_c", "c3"],
        vector_top_k=["c1", "c3"],
        reranked_top_k=["target_c", "c1"],
        expected_pages=[3],
        retrieved_pages=[3, 1],
    )
    assert res_success == "success"

    # 3. Reranking failure (vector search had target in top-5, but reranker pushed it out)
    res_rerank_fail = classify_evaluation_error(
        is_unanswerable=False,
        expected_chunk_ids=["target_c"],
        all_candidates=["target_c", "c1", "c2", "c3", "c4", "c5"],
        vector_top_k=["target_c", "c1", "c2"],
        reranked_top_k=["c1", "c2", "c3", "c4", "c5"],
        expected_pages=[3],
        retrieved_pages=[1, 2, 4],
    )
    assert res_rerank_fail == "reranking_failure"

    # 4. Retrieval failure (target chunk not retrieved in candidates at all)
    res_retrieval_fail = classify_evaluation_error(
        is_unanswerable=False,
        expected_chunk_ids=["target_c"],
        all_candidates=["c1", "c2", "c3"],
        vector_top_k=["c1", "c2"],
        reranked_top_k=["c1", "c2"],
        expected_pages=[3],
        retrieved_pages=[1, 2],
    )
    assert res_retrieval_fail == "retrieval_failure"
