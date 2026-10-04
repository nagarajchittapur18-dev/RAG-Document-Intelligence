"""
Integration tests for Phase 12 Academic Evaluation API endpoints,
dataset validation logic, and benchmark execution runner.
"""

import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from app.main import app
from app.services.document_store import DatabaseManager
from app.services.evaluation_engine import EvaluationEngine
from evaluation.scripts.validate_dataset import DatasetValidator

client = TestClient(app)
db = DatabaseManager()


@pytest.fixture(scope="module")
def auth_headers():
    """Creates a verified test user and returns bearer token headers."""
    import uuid
    unique_suffix = uuid.uuid4().hex[:6]
    email = f"eval_tester_{unique_suffix}@ragmate.edu"
    pwd = "EvalPassword123!"
    client.post(
        "/api/auth/register",
        json={"email": email, "password": pwd, "name": "Academic Evaluator"},
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": pwd},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dataset_validator_success_and_failures(tmp_path):
    # 1. Valid dataset sample
    valid_sample = [
        {
            "id": "Q_TEST_01",
            "question": "What is the vector dimension?",
            "document_id": "eval_doc_01",
            "document_name": "rag_dense_retrieval.pdf",
            "expected_pages": [5],
            "expected_chunk_ids": ["doc_eval_doc_01_p5_c0"],
            "reference_answer": "The model produces 384-dimensional vectors.",
            "question_type": "fact",
            "difficulty": "easy",
        },
        {
            "id": "Q_TEST_02",
            "question": "What was company revenue in 2024?",
            "document_id": "eval_doc_01",
            "document_name": "rag_dense_retrieval.pdf",
            "expected_pages": [],
            "expected_chunk_ids": [],
            "reference_answer": "I could not find sufficient information in the selected documents to answer this question.",
            "question_type": "unanswerable",
            "difficulty": "easy",
        },
    ]

    validator = DatasetValidator(verify_chunks=False)
    v_res = validator.validate(dataset=valid_sample)
    assert v_res["is_valid"] is True
    assert v_res["valid_count"] == 2
    assert v_res["invalid_count"] == 0

    # 2. Invalid sample: duplicate ID, missing field, invalid question type
    invalid_sample = [
        {
            "id": "Q_DUP",
            "question": "First question",
            "document_id": "doc1",
            "document_name": "doc.pdf",
            "expected_pages": [1],
            "expected_chunk_ids": ["c1"],
            "reference_answer": "Answer 1",
            "question_type": "fact",
            "difficulty": "easy",
        },
        {
            "id": "Q_DUP",  # Duplicate ID
            "question": "Second question",
            # Missing document_id
            "document_name": "doc.pdf",
            "expected_pages": [1],
            "expected_chunk_ids": ["c1"],
            "reference_answer": "Answer 2",
            "question_type": "invalid_type_name",  # Invalid type
            "difficulty": "super_hard",  # Invalid difficulty
        },
    ]

    inv_res = validator.validate(dataset=invalid_sample)
    assert inv_res["is_valid"] is False
    assert inv_res["invalid_count"] > 0
    assert any("duplicate question ID" in e for e in inv_res["errors"])
    assert any("invalid 'question_type'" in e for e in inv_res["errors"])
    assert any("invalid 'difficulty'" in e for e in inv_res["errors"])


def test_api_dataset_summary_endpoint(auth_headers):
    res = client.get("/api/evaluation/dataset/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_questions"] == 60
    assert data["unanswerable_count"] == 6
    assert data["answerable_count"] == 54
    assert data["dataset_version"] == "v1.0"
    assert "fact" in data["by_type"]
    assert "comparison" in data["by_type"]
    assert "easy" in data["by_difficulty"]


def test_api_run_benchmark_fast_subset(auth_headers):
    # Run fast benchmark on a subset of 3 questions
    req_payload = {
        "candidate_k": 10,
        "k_values": [1, 3, 5],
        "limit": 3,
    }
    res = client.post("/api/evaluation/run-benchmark", json=req_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "experiment_id" in data
    assert data["questions_evaluated"] == 3
    assert "baseline_vector" in data
    assert "enhanced_reranked" in data
    assert "improvements" in data
    assert len(data["improvements"]) >= 4

    exp_id = data["experiment_id"]

    # Verify experiment is listed in GET /api/evaluation/experiments
    list_res = client.get("/api/evaluation/experiments", headers=auth_headers)
    assert list_res.status_code == 200
    exp_list = list_res.json()
    assert any(e["experiment_id"] == exp_id for e in exp_list)

    # Verify detail retrieval in GET /api/evaluation/experiments/{id}
    detail_res = client.get(f"/api/evaluation/experiments/{exp_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["experiment_id"] == exp_id
    assert "baseline_vector" in detail_data


def test_api_experiment_detail_not_found(auth_headers):
    res = client.get("/api/evaluation/experiments/NON_EXISTENT_EXPERIMENT_999", headers=auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_evaluation_engine_single_query_output():
    engine = EvaluationEngine()
    result = engine.evaluate_single_query(
        query="What is the vector dimension?",
        expected_chunk_ids=["doc_eval_doc_01_p5_c0"],
        expected_pages=[5],
        expected_doc_ids=["eval_doc_01"],
        candidate_k=10,
        k_values=[1, 3, 5],
    )

    assert "query" in result
    assert "vector_latency_ms" in result
    assert "rerank_latency_ms" in result
    assert "total_latency_ms" in result
    assert "vector_only" in result
    assert "reranked" in result

    vec_mrr = result["vector_only"]["mrr"]
    rerank_mrr = result["reranked"]["mrr"]
    assert 0.0 <= vec_mrr <= 1.0
    assert 0.0 <= rerank_mrr <= 1.0


def test_api_experiment_queries_pagination_and_filter(auth_headers):
    # Fetch experiments list first to get an existing experiment id
    list_res = client.get("/api/evaluation/experiments", headers=auth_headers)
    assert list_res.status_code == 200
    exps = list_res.json()
    assert len(exps) > 0
    exp_id = exps[0]["experiment_id"]

    # 1. Plain queries endpoint
    res = client.get(f"/api/evaluation/experiments/{exp_id}/queries", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0
    first_item = data["items"][0]
    assert "id" in first_item
    assert "question" in first_item

    # 2. Filter by question_type
    res_type = client.get(
        f"/api/evaluation/experiments/{exp_id}/queries",
        params={"question_type": "fact"},
        headers=auth_headers,
    )
    assert res_type.status_code == 200
    fact_items = res_type.json()["items"]
    assert all(item["question_type"] == "fact" for item in fact_items)

    # 3. Search filter
    res_search = client.get(
        f"/api/evaluation/experiments/{exp_id}/queries",
        params={"search": "vector"},
        headers=auth_headers,
    )
    assert res_search.status_code == 200
    search_items = res_search.json()["items"]
    assert all("vector" in item["question"].lower() or "vector" in item["id"].lower() for item in search_items)


def test_api_experiment_error_analysis(auth_headers):
    list_res = client.get("/api/evaluation/experiments", headers=auth_headers)
    assert list_res.status_code == 200
    exp_id = list_res.json()[0]["experiment_id"]

    res = client.get(f"/api/evaluation/experiments/{exp_id}/error-analysis", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "error_counts" in data
    assert "success" in data["error_counts"]
    assert "detailed_failures" in data


def test_api_experiment_export_csv_and_json(auth_headers):
    list_res = client.get("/api/evaluation/experiments", headers=auth_headers)
    assert list_res.status_code == 200
    exp_id = list_res.json()[0]["experiment_id"]

    # CSV Export
    res_csv = client.get(
        f"/api/evaluation/experiments/{exp_id}/export",
        params={"format": "csv"},
        headers=auth_headers,
    )
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "attachment" in res_csv.headers["content-disposition"]
    csv_text = res_csv.text
    assert "id,question,question_type" in csv_text

    # JSON Export
    res_json = client.get(
        f"/api/evaluation/experiments/{exp_id}/export",
        params={"format": "json"},
        headers=auth_headers,
    )
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]
    json_data = res_json.json()
    assert isinstance(json_data, list)
    assert len(json_data) > 0


def test_api_dataset_question_detail(auth_headers):
    # Valid Question ID (both exact Q001 and normalized Q01)
    res = client.get("/api/evaluation/dataset/questions/Q001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "Q001"
    assert "question" in data
    assert "reference_answer" in data
    assert "expected_chunk_ids" in data

    # Normalized short ID
    res_norm = client.get("/api/evaluation/dataset/questions/Q01", headers=auth_headers)
    assert res_norm.status_code == 200
    assert res_norm.json()["id"] == "Q001"

    # Non-existent Question ID
    res_404 = client.get("/api/evaluation/dataset/questions/NON_EXISTENT_Q999", headers=auth_headers)
    assert res_404.status_code == 404

