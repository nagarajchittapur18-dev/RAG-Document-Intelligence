import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.evaluation import (
    BenchmarkRunRequest,
    BenchmarkRunResponse,
    EvaluationChunkItem,
    EvaluationDatasetSummaryResponse,
    ExperimentListItem,
    RetrievalCompareRequest,
    RetrievalCompareResponse,
)
from app.services.document_store import DatabaseManager, UserRecord
from app.services.evaluation_engine import (
    DEFAULT_DATASET_PATH,
    REPORTS_DIR,
    RESULTS_DIR,
    EvaluationEngine,
)
from app.services.reranker import RerankerService
from app.services.vector_store import VectorStore
from app.utils.dependencies import get_current_user

logger = logging.getLogger("ragmate.api.evaluation")
router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarking"])

vector_store = VectorStore()
reranker_service = RerankerService()
db = DatabaseManager()
eval_engine = EvaluationEngine()


# =====================================================================
# Existing Phase 11 Retrieval Compare Endpoint (Preserved 100%)
# =====================================================================

@router.post(
    "/retrieval-compare",
    response_model=RetrievalCompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Vector-Only retrieval vs Vector + Cross-Encoder Reranking",
    description="Academic research endpoint evaluating the impact of two-stage retrieval. Returns both vector-ranked and cross-encoder reranked candidate lists with individual latency benchmarks.",
)
async def compare_retrieval_methods(
    request: RetrievalCompareRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    clean_query = request.question.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    # Validate document IDs ownership
    valid_doc_ids: Optional[List[str]] = None
    if request.document_ids:
        valid_doc_ids = []
        for doc_id in request.document_ids:
            doc = db.get_document(doc_id)
            if not doc or doc.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{doc_id}' not found or unauthorized.",
                )
            valid_doc_ids.append(doc_id)

    num_docs = len(valid_doc_ids) if valid_doc_ids else len(db.list_documents_for_user(current_user.id))
    candidate_k = request.candidate_k or 15
    final_k = request.final_k or 5

    # 1. Measure Vector Retrieval Latency
    t_v0 = time.perf_counter()
    candidates = vector_store.similarity_search(
        query_text=clean_query,
        top_k=candidate_k,
        document_ids=valid_doc_ids,
        user_id=current_user.id,
    )
    vector_latency_ms = (time.perf_counter() - t_v0) * 1000

    # Deduplicate candidates
    seen = set()
    unique_candidates = []
    for c in candidates:
        key = (str(c.document_id), str(c.chunk_id))
        if key not in seen:
            seen.add(key)
            unique_candidates.append(c)

    # Method A: Vector-Only Top-K
    vector_only_sorted = sorted(unique_candidates, key=lambda x: x.similarity_score, reverse=True)[:final_k]
    vector_items = [
        EvaluationChunkItem(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            document_name=c.document_name,
            page_number=c.page_number,
            text=c.text,
            similarity_score=round(c.similarity_score, 4),
            rerank_score=None,
            rank=idx + 1,
        )
        for idx, c in enumerate(vector_only_sorted)
    ]

    # Method B: Vector + Cross-Encoder Reranking
    t_r0 = time.perf_counter()
    reranked_pool = reranker_service.rerank(
        query=clean_query,
        candidates=[c.model_copy() for c in unique_candidates],
        top_k=final_k,
    )
    rerank_latency_ms = (time.perf_counter() - t_r0) * 1000

    reranked_items = [
        EvaluationChunkItem(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            document_name=c.document_name,
            page_number=c.page_number,
            text=c.text,
            similarity_score=round(c.similarity_score, 4),
            rerank_score=round(c.rerank_score, 4) if c.rerank_score is not None else None,
            rank=idx + 1,
        )
        for idx, c in enumerate(reranked_pool)
    ]

    total_latency_ms = vector_latency_ms + rerank_latency_ms

    return RetrievalCompareResponse(
        question=clean_query,
        documents_searched=num_docs,
        candidate_count=len(unique_candidates),
        vector_only_chunks=vector_items,
        reranked_chunks=reranked_items,
        vector_latency_ms=round(vector_latency_ms, 2),
        rerank_latency_ms=round(rerank_latency_ms, 2),
        total_latency_ms=round(total_latency_ms, 2),
    )


# =====================================================================
# Phase 12 Academic Quantitative Evaluation Endpoints
# =====================================================================

@router.get(
    "/dataset/summary",
    response_model=EvaluationDatasetSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get summary metrics of the academic evaluation benchmark dataset",
)
async def get_dataset_summary(
    current_user: UserRecord = Depends(get_current_user),
):
    if not DEFAULT_DATASET_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation dataset not found on disk.",
        )

    with open(DEFAULT_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    by_type = {}
    by_diff = {}
    by_doc = {}
    unanswerable = 0

    for item in data:
        t = item.get("question_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

        d = item.get("difficulty", "medium")
        by_diff[d] = by_diff.get(d, 0) + 1

        doc = item.get("document_name", "unknown")
        by_doc[doc] = by_doc.get(doc, 0) + 1

        if t == "unanswerable":
            unanswerable += 1

    return EvaluationDatasetSummaryResponse(
        total_questions=len(data),
        by_type=by_type,
        by_difficulty=by_diff,
        by_document=by_doc,
        unanswerable_count=unanswerable,
        answerable_count=len(data) - unanswerable,
        dataset_version="v1.0",
    )


@router.post(
    "/run-benchmark",
    response_model=BenchmarkRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute comprehensive academic evaluation benchmark",
)
async def run_benchmark_endpoint(
    request: BenchmarkRunRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    dataset = None
    if request.dataset_path:
        p = Path(request.dataset_path)
        if not p.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specified dataset path '{request.dataset_path}' not found.",
            )
        with open(p, "r", encoding="utf-8") as f:
            dataset = json.load(f)

    try:
        summary = eval_engine.run_benchmark(
            dataset=dataset,
            candidate_k=request.candidate_k or 15,
            k_values=request.k_values or [1, 3, 5, 10],
            limit=request.limit,
        )
    except Exception as e:
        logger.exception("Benchmark run failed with error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark execution failed: {str(e)}",
        )

    exp_id = summary["experiment_id"]
    return BenchmarkRunResponse(
        experiment_id=exp_id,
        timestamp=summary["timestamp"],
        dataset_version=summary["dataset_version"],
        questions_evaluated=summary["questions_evaluated"],
        baseline_vector=summary["baseline_vector"],
        enhanced_reranked=summary["enhanced_reranked"],
        improvements=summary["improvements"],
        error_summary=summary["error_summary"],
        summary_path=str(RESULTS_DIR / f"{exp_id}_summary.json"),
    )


@router.get(
    "/experiments",
    response_model=List[ExperimentListItem],
    status_code=status.HTTP_200_OK,
    summary="List all recorded academic benchmark experiments",
)
async def list_experiments(
    current_user: UserRecord = Depends(get_current_user),
):
    if not RESULTS_DIR.exists():
        return []

    experiments: List[ExperimentListItem] = []
    for file_path in sorted(RESULTS_DIR.glob("*_summary.json"), reverse=True):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            vec = data.get("baseline_vector", {})
            rerank = data.get("enhanced_reranked", {})
            imps = {i["metric"]: i["improvement_percentage"] for i in data.get("improvements", [])}

            experiments.append(
                ExperimentListItem(
                    experiment_id=data.get("experiment_id", file_path.stem),
                    timestamp=data.get("timestamp", ""),
                    dataset_version=data.get("dataset_version", "v1.0"),
                    questions_evaluated=data.get("questions_evaluated", 0),
                    vector_mrr=vec.get("mrr", 0.0),
                    reranked_mrr=rerank.get("mrr", 0.0),
                    mrr_improvement_pct=imps.get("MRR", 0.0),
                    vector_hit5=vec.get("metrics_by_k", {}).get("K=5", {}).get("hit_rate", 0.0),
                    reranked_hit5=rerank.get("metrics_by_k", {}).get("K=5", {}).get("hit_rate", 0.0),
                    hit5_improvement_pct=imps.get("Hit Rate@5", 0.0),
                    avg_latency_ms=rerank.get("avg_total_latency_ms", 0.0),
                )
            )
        except Exception as e:
            logger.warning("Could not read experiment artifact %s: %s", file_path.name, str(e))

    return experiments


@router.get(
    "/experiments/{experiment_id}",
    status_code=status.HTTP_200_OK,
    summary="Get complete raw results and configuration for a specific experiment",
)
async def get_experiment_detail(
    experiment_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    clean_id = experiment_id.strip()
    target_file = RESULTS_DIR / f"{clean_id}_summary.json"
    if not target_file.exists():
        target_file = RESULTS_DIR / f"{clean_id}.json"
    if not target_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{clean_id}' not found.",
        )

    with open(target_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


@router.get(
    "/experiments/{experiment_id}/queries",
    status_code=status.HTTP_200_OK,
    summary="Get question-level results for a specific experiment with optional filtering and pagination",
)
async def get_experiment_queries(
    experiment_id: str,
    search: Optional[str] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    error_classification: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: UserRecord = Depends(get_current_user),
):
    clean_id = experiment_id.strip()
    target_file = RESULTS_DIR / f"{clean_id}_queries.json"
    if not target_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queries artifact for experiment '{clean_id}' not found.",
        )

    with open(target_file, "r", encoding="utf-8") as f:
        queries = json.load(f)

    filtered = queries
    if search:
        s_lower = search.strip().lower()
        filtered = [
            q for q in filtered
            if s_lower in q.get("id", "").lower()
            or s_lower in q.get("question", "").lower()
        ]
    if question_type and question_type.lower() != "all":
        filtered = [q for q in filtered if q.get("question_type") == question_type]
    if difficulty and difficulty.lower() != "all":
        filtered = [q for q in filtered if q.get("difficulty") == difficulty]
    if error_classification and error_classification.lower() != "all":
        filtered = [q for q in filtered if q.get("error_classification") == error_classification]

    total_count = len(filtered)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = filtered[start_idx:end_idx]

    return {
        "experiment_id": clean_id,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "items": paged_items,
    }


@router.get(
    "/experiments/{experiment_id}/error-analysis",
    status_code=status.HTTP_200_OK,
    summary="Get error analysis report for an experiment",
)
async def get_experiment_error_analysis(
    experiment_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    clean_id = experiment_id.strip()
    target_file = REPORTS_DIR / f"{clean_id}_error_analysis.json"
    if not target_file.exists():
        target_file = REPORTS_DIR / "error_analysis.json"
    if not target_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error analysis for experiment '{clean_id}' not found.",
        )

    with open(target_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@router.get(
    "/experiments/{experiment_id}/export",
    summary="Export experiment questions and metrics in CSV or JSON format",
)
async def export_experiment(
    experiment_id: str,
    format: str = "json",
    current_user: UserRecord = Depends(get_current_user),
):
    clean_id = experiment_id.strip()
    target_file = RESULTS_DIR / f"{clean_id}_queries.json"
    if not target_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queries artifact for experiment '{clean_id}' not found.",
        )

    with open(target_file, "r", encoding="utf-8") as f:
        queries = json.load(f)

    if format.lower() == "csv":
        import csv
        import io
        from fastapi.responses import Response

        output = io.StringIO()
        fieldnames = [
            "id", "question", "question_type", "difficulty",
            "vector_mrr", "reranked_mrr", "vector_latency_ms",
            "rerank_latency_ms", "total_latency_ms", "error_classification"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for q in queries:
            writer.writerow(q)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{clean_id}_results.csv"'},
        )

    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=queries,
        headers={"Content-Disposition": f'attachment; filename="{clean_id}_results.json"'},
    )


@router.get(
    "/dataset/questions/{question_id}",
    status_code=status.HTTP_200_OK,
    summary="Get full metadata and reference answer for a specific evaluation question",
)
async def get_question_detail(
    question_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    if not DEFAULT_DATASET_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation dataset not found on disk.",
        )

    with open(DEFAULT_DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    clean_qid = question_id.strip().upper()
    for item in dataset:
        if item.get("id", "").upper() == clean_qid:
            return item

    # Flexible numeric normalization (e.g. Q1 or Q01 matching Q001)
    if clean_qid.startswith("Q") and clean_qid[1:].isdigit():
        num = int(clean_qid[1:])
        padded_variants = {f"Q{num:03d}", f"Q{num:02d}", f"Q{num}"}
        for item in dataset:
            if item.get("id", "").upper() in padded_variants:
                return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Evaluation question '{question_id}' not found in dataset.",
    )

