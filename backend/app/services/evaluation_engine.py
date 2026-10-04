"""
Academic Evaluation Engine for DocuRAG / RAGMate Phase 12.
Computes formal Information Retrieval (IR) metrics (Precision@K, Recall@K, Hit Rate@K, MRR),
page/document-level metrics, latency benchmarks, abstention accuracy, and error analyses.
Evaluates both Baseline (Vector-Only) and Enhanced (Vector + Cross-Encoder Reranking).
"""

import json
import logging
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.config import settings
from app.services.reranker import RerankerService
from app.services.vector_store import SearchResult, VectorStore

logger = logging.getLogger("ragmate.evaluation_engine")

EVAL_COLLECTION_NAME = "ragmate_eval_collection"
DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "evaluation"
    / "dataset"
    / "evaluation_questions.json"
)
RESULTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "evaluation" / "results"
REPORTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "evaluation" / "reports"


# =====================================================================
# 1. Standalone Pure IR Metric Functions
# =====================================================================

def deduplicate_list(items: List[Any]) -> List[Any]:
    """Preserves order while removing duplicate occurrences."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def compute_precision_at_k(
    retrieved_chunk_ids: List[str],
    expected_chunk_ids: List[str],
    k: int,
) -> float:
    """
    Precision@K = |Retrieved@K ∩ Relevant| / K
    """
    if k <= 0:
        return 0.0

    unique_retrieved = deduplicate_list(retrieved_chunk_ids)[:k]
    expected_set = set(expected_chunk_ids)

    if not expected_set:
        # For unanswerable queries where no chunk is relevant
        return 1.0 if len(unique_retrieved) == 0 else 0.0

    hits = sum(1 for c in unique_retrieved if c in expected_set)
    return round(hits / k, 4)


def compute_recall_at_k(
    retrieved_chunk_ids: List[str],
    expected_chunk_ids: List[str],
    k: int,
) -> float:
    """
    Recall@K = |Retrieved@K ∩ Relevant| / |Relevant|
    """
    expected_set = set(expected_chunk_ids)
    if not expected_set:
        return 0.0

    unique_retrieved = deduplicate_list(retrieved_chunk_ids)[:k]
    hits = sum(1 for c in unique_retrieved if c in expected_set)
    return round(hits / len(expected_set), 4)


def compute_hit_rate_at_k(
    retrieved_chunk_ids: List[str],
    expected_chunk_ids: List[str],
    k: int,
) -> float:
    """
    Hit Rate@K = 1.0 if |Retrieved@K ∩ Relevant| > 0 else 0.0
    """
    expected_set = set(expected_chunk_ids)
    if not expected_set:
        return 0.0

    unique_retrieved = deduplicate_list(retrieved_chunk_ids)[:k]
    return 1.0 if any(c in expected_set for c in unique_retrieved) else 0.0


def compute_reciprocal_rank(
    retrieved_chunk_ids: List[str],
    expected_chunk_ids: List[str],
) -> float:
    """
    RR = 1 / rank of first relevant chunk retrieved (1-indexed).
    Returns 0.0 if no relevant chunk is retrieved.
    """
    expected_set = set(expected_chunk_ids)
    if not expected_set or not retrieved_chunk_ids:
        return 0.0

    for rank, chunk_id in enumerate(deduplicate_list(retrieved_chunk_ids), start=1):
        if chunk_id in expected_set:
            return round(1.0 / rank, 4)
    return 0.0


def compute_page_hit_rate_at_k(
    retrieved_pages: List[int],
    expected_pages: List[int],
    k: int,
) -> float:
    """
    Page Hit Rate@K = 1.0 if any retrieved chunk in top K comes from expected pages.
    """
    expected_set = set(expected_pages)
    if not expected_set:
        return 0.0

    top_pages = retrieved_pages[:k]
    return 1.0 if any(p in expected_set for p in top_pages) else 0.0


def compute_document_hit_rate_at_k(
    retrieved_doc_ids: List[str],
    expected_doc_ids: List[str],
    k: int,
) -> float:
    """
    Document Hit Rate@K = 1.0 if any retrieved chunk in top K comes from expected documents.
    """
    expected_set = set(str(d) for d in expected_doc_ids)
    if not expected_set:
        return 0.0

    top_docs = [str(d) for d in retrieved_doc_ids[:k]]
    return 1.0 if any(d in expected_set for d in top_docs) else 0.0


def compute_abstention_accuracy(
    is_unanswerable: bool,
    answer_text: Optional[str] = None,
    candidate_max_similarity: Optional[float] = None,
    threshold: float = 0.15,
) -> float:
    """
    Measures whether the system appropriately abstains on unanswerable queries
    and provides responses for answerable queries.
    """
    ABSTENTION_MARKERS = [
        "could not find sufficient information",
        "cannot find sufficient information",
        "not enough information",
        "does not contain information",
        "no information in the selected documents",
    ]

    did_abstain = False
    if answer_text:
        lower_ans = answer_text.lower()
        did_abstain = any(marker in lower_ans for marker in ABSTENTION_MARKERS)
    elif candidate_max_similarity is not None:
        did_abstain = candidate_max_similarity < threshold

    if is_unanswerable:
        return 1.0 if did_abstain else 0.0
    else:
        return 1.0 if not did_abstain else 0.0


def calculate_improvement_percentage(baseline: float, reranked: float) -> float:
    """
    Improvement % = ((Reranked - Baseline) / Baseline) * 100
    Handles zero division safely.
    """
    if baseline == 0.0:
        if reranked > 0.0:
            return 100.0
        elif reranked == 0.0:
            return 0.0
        else:
            return -100.0
    return round(((reranked - baseline) / baseline) * 100.0, 2)


def compute_statistical_summary(values: List[float]) -> Dict[str, float]:
    """Calculates mean, median, min, max, and standard deviation."""
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "std_dev": 0.0}

    mean_val = round(statistics.mean(values), 4)
    med_val = round(statistics.median(values), 4)
    min_val = round(min(values), 4)
    max_val = round(max(values), 4)
    std_val = round(statistics.stdev(values), 4) if len(values) >= 2 else 0.0

    return {
        "mean": mean_val,
        "median": med_val,
        "min": min_val,
        "max": max_val,
        "std_dev": std_val,
    }


def classify_evaluation_error(
    is_unanswerable: bool,
    expected_chunk_ids: List[str],
    all_candidates: List[str],
    vector_top_k: List[str],
    reranked_top_k: List[str],
    expected_pages: List[int],
    retrieved_pages: List[int],
    answer_text: Optional[str] = None,
    max_relevance_score: Optional[float] = None,
    abstention_threshold: float = 0.15,
) -> str:
    """
    Classifies the outcome of an individual evaluation question.
    """
    if is_unanswerable:
        abstention = compute_abstention_accuracy(
            is_unanswerable=True,
            answer_text=answer_text,
            candidate_max_similarity=max_relevance_score,
            threshold=abstention_threshold,
        )
        return "unanswerable_abstention_success" if abstention == 1.0 else "abstention_failure"

    expected_set = set(expected_chunk_ids)
    in_reranked_top = any(c in expected_set for c in reranked_top_k)
    in_vector_top = any(c in expected_set for c in vector_top_k)
    in_candidates = any(c in expected_set for c in all_candidates)

    if in_reranked_top:
        return "success"
    elif in_vector_top and not in_reranked_top:
        return "reranking_failure"
    elif not in_candidates:
        return "retrieval_failure"
    else:
        # In candidates but outside top-K for both
        if expected_pages and not any(p in set(expected_pages) for p in retrieved_pages):
            return "page_mismatch"
        return "retrieval_failure"


# =====================================================================
# 2. Main Evaluation Engine Class
# =====================================================================

class EvaluationEngine:
    """
    Reproducible academic evaluation runner.
    Compares Vector Retrieval Only vs Vector + Cross-Encoder Reranking
    over the evaluation benchmark dataset.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        reranker: Optional[RerankerService] = None,
        collection_name: str = EVAL_COLLECTION_NAME,
    ):
        self.vector_store = vector_store or VectorStore(collection_name=collection_name)
        self.reranker = reranker or RerankerService()
        self.collection_name = collection_name
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def evaluate_single_query(
        self,
        query: str,
        expected_chunk_ids: List[str],
        expected_pages: List[int],
        expected_doc_ids: List[str],
        candidate_k: int = 15,
        k_values: Optional[List[int]] = None,
        selected_doc_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs dual-stage evaluation for a single question:
        Executes vector search (candidate pool), followed by cross-encoder reranking.
        Computes IR metrics at each K for both methods.
        """
        k_list = k_values or [1, 3, 5, 10]
        max_k = max(max(k_list), candidate_k)

        # 1. Vector Search
        t_v0 = time.perf_counter()
        raw_candidates = self.vector_store.similarity_search(
            query_text=query,
            top_k=max_k,
            document_ids=selected_doc_ids,
            user_id=user_id,
        )
        vector_latency_ms = (time.perf_counter() - t_v0) * 1000.0

        # Deduplicate candidates preserving vector order
        seen = set()
        unique_candidates: List[SearchResult] = []
        for c in raw_candidates:
            key = (str(c.document_id), str(c.chunk_id))
            if key not in seen:
                seen.add(key)
                unique_candidates.append(c)

        # Baseline: Vector Only Top-K
        vector_chunk_ids = [c.chunk_id for c in unique_candidates]
        vector_pages = [c.page_number for c in unique_candidates]
        vector_docs = [c.document_id for c in unique_candidates]

        # 2. Cross-Encoder Reranking
        t_r0 = time.perf_counter()
        reranked_pool = self.reranker.rerank(
            query=query,
            candidates=[c.model_copy() for c in unique_candidates],
            top_k=max_k,
        )
        rerank_latency_ms = (time.perf_counter() - t_r0) * 1000.0

        reranked_chunk_ids = [c.chunk_id for c in reranked_pool]
        reranked_pages = [c.page_number for c in reranked_pool]
        reranked_docs = [c.document_id for c in reranked_pool]

        # Calculate metrics for each configuration
        vector_metrics = {}
        reranked_metrics = {}

        for k in k_list:
            vector_metrics[f"K={k}"] = {
                "precision": compute_precision_at_k(vector_chunk_ids, expected_chunk_ids, k),
                "recall": compute_recall_at_k(vector_chunk_ids, expected_chunk_ids, k),
                "hit_rate": compute_hit_rate_at_k(vector_chunk_ids, expected_chunk_ids, k),
                "page_hit_rate": compute_page_hit_rate_at_k(vector_pages, expected_pages, k),
                "doc_hit_rate": compute_document_hit_rate_at_k(vector_docs, expected_doc_ids, k),
            }
            reranked_metrics[f"K={k}"] = {
                "precision": compute_precision_at_k(reranked_chunk_ids, expected_chunk_ids, k),
                "recall": compute_recall_at_k(reranked_chunk_ids, expected_chunk_ids, k),
                "hit_rate": compute_hit_rate_at_k(reranked_chunk_ids, expected_chunk_ids, k),
                "page_hit_rate": compute_page_hit_rate_at_k(reranked_pages, expected_pages, k),
                "doc_hit_rate": compute_document_hit_rate_at_k(reranked_docs, expected_doc_ids, k),
            }

        vector_mrr = compute_reciprocal_rank(vector_chunk_ids, expected_chunk_ids)
        reranked_mrr = compute_reciprocal_rank(reranked_chunk_ids, expected_chunk_ids)

        max_v_score = max([c.similarity_score for c in unique_candidates], default=0.0)
        max_r_score = max([c.rerank_score for c in reranked_pool if c.rerank_score is not None], default=0.0)

        return {
            "query": query,
            "vector_latency_ms": round(vector_latency_ms, 2),
            "rerank_latency_ms": round(rerank_latency_ms, 2),
            "total_latency_ms": round(vector_latency_ms + rerank_latency_ms, 2),
            "candidates_retrieved": len(unique_candidates),
            "vector_max_score": round(max_v_score, 4),
            "rerank_max_score": round(max_r_score, 4),
            "vector_only": {
                "chunk_ids": vector_chunk_ids[:10],
                "pages": vector_pages[:10],
                "mrr": vector_mrr,
                "metrics_by_k": vector_metrics,
            },
            "reranked": {
                "chunk_ids": reranked_chunk_ids[:10],
                "pages": reranked_pages[:10],
                "mrr": reranked_mrr,
                "metrics_by_k": reranked_metrics,
            },
        }

    def run_benchmark(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        candidate_k: int = 15,
        k_values: Optional[List[int]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes full benchmark evaluation across the dataset.
        Produces full metrics, comparative tables, error analysis, and persists results.
        """
        k_list = k_values or [1, 3, 5, 10]

        if dataset is None:
            if not DEFAULT_DATASET_PATH.exists():
                raise FileNotFoundError(f"Evaluation dataset not found at {DEFAULT_DATASET_PATH}")
            with open(DEFAULT_DATASET_PATH, "r", encoding="utf-8") as f:
                dataset = json.load(f)

        if limit and limit > 0:
            dataset = dataset[:limit]

        now_utc = datetime.now(timezone.utc)
        exp_id = f"EXP_{now_utc.strftime('%Y%m%d_%H%M%S')}_{len(dataset)}"
        dataset_version = "v1.0"

        logger.info("Starting benchmark %s with %d questions...", exp_id, len(dataset))

        vector_latencies = []
        rerank_latencies = []
        total_latencies = []

        vector_mrrs = []
        reranked_mrrs = []

        # Metric accumulators: method -> metric_name -> k -> list of values
        vec_k_accum: Dict[int, Dict[str, List[float]]] = {
            k: {"precision": [], "recall": [], "hit_rate": [], "page_hit": [], "doc_hit": []}
            for k in k_list
        }
        rerank_k_accum: Dict[int, Dict[str, List[float]]] = {
            k: {"precision": [], "recall": [], "hit_rate": [], "page_hit": [], "doc_hit": []}
            for k in k_list
        }

        # Breakdown by question type
        by_type_mrr: Dict[str, Dict[str, List[float]]] = {}

        # Error analysis collector
        error_classifications: Dict[str, int] = {
            "success": 0,
            "reranking_failure": 0,
            "retrieval_failure": 0,
            "page_mismatch": 0,
            "unanswerable_abstention_success": 0,
            "abstention_failure": 0,
        }
        detailed_error_reports: List[Dict[str, Any]] = []
        per_query_results: List[Dict[str, Any]] = []

        for item in dataset:
            q_id = item["id"]
            question = item["question"]
            expected_chunks = item.get("expected_chunk_ids", [])
            expected_pages = item.get("expected_pages", [])
            q_type = item.get("question_type", "fact")
            selected_docs = item.get("selected_document_ids") or (
                [item["document_id"]] if "document_id" in item else None
            )
            expected_docs = selected_docs or []
            is_unanswerable = q_type == "unanswerable"

            # Run evaluation for this query
            eval_res = self.evaluate_single_query(
                query=question,
                expected_chunk_ids=expected_chunks,
                expected_pages=expected_pages,
                expected_doc_ids=expected_docs,
                candidate_k=candidate_k,
                k_values=k_list,
                selected_doc_ids=selected_docs,
            )

            v_lat = eval_res["vector_latency_ms"]
            r_lat = eval_res["rerank_latency_ms"]
            tot_lat = eval_res["total_latency_ms"]

            vector_latencies.append(v_lat)
            rerank_latencies.append(r_lat)
            total_latencies.append(tot_lat)

            v_mrr = eval_res["vector_only"]["mrr"]
            r_mrr = eval_res["reranked"]["mrr"]

            # Only accumulate retrieval ranking metrics for answerable questions
            if not is_unanswerable:
                vector_mrrs.append(v_mrr)
                reranked_mrrs.append(r_mrr)

                if q_type not in by_type_mrr:
                    by_type_mrr[q_type] = {"vector": [], "reranked": []}
                by_type_mrr[q_type]["vector"].append(v_mrr)
                by_type_mrr[q_type]["reranked"].append(r_mrr)

                for k in k_list:
                    vk = eval_res["vector_only"]["metrics_by_k"][f"K={k}"]
                    vec_k_accum[k]["precision"].append(vk["precision"])
                    vec_k_accum[k]["recall"].append(vk["recall"])
                    vec_k_accum[k]["hit_rate"].append(vk["hit_rate"])
                    vec_k_accum[k]["page_hit"].append(vk["page_hit_rate"])
                    vec_k_accum[k]["doc_hit"].append(vk["doc_hit_rate"])

                    rk = eval_res["reranked"]["metrics_by_k"][f"K={k}"]
                    rerank_k_accum[k]["precision"].append(rk["precision"])
                    rerank_k_accum[k]["recall"].append(rk["recall"])
                    rerank_k_accum[k]["hit_rate"].append(rk["hit_rate"])
                    rerank_k_accum[k]["page_hit"].append(rk["page_hit_rate"])
                    rerank_k_accum[k]["doc_hit"].append(rk["doc_hit_rate"])

            # Error analysis
            vector_top_5 = eval_res["vector_only"]["chunk_ids"][:5]
            reranked_top_5 = eval_res["reranked"]["chunk_ids"][:5]
            retrieved_pages_5 = eval_res["reranked"]["pages"][:5]
            all_cands = eval_res["vector_only"]["chunk_ids"]

            # Abstention simulation for unanswerable questions:
            # If highest similarity candidate < 0.15 threshold, consider abstained
            err_class = classify_evaluation_error(
                is_unanswerable=is_unanswerable,
                expected_chunk_ids=expected_chunks,
                all_candidates=all_cands,
                vector_top_k=vector_top_5,
                reranked_top_k=reranked_top_5,
                expected_pages=expected_pages,
                retrieved_pages=retrieved_pages_5,
                max_relevance_score=eval_res["rerank_max_score"],
                abstention_threshold=0.15,
            )
            error_classifications[err_class] = error_classifications.get(err_class, 0) + 1

            if err_class != "success" and err_class != "unanswerable_abstention_success":
                detailed_error_reports.append(
                    {
                        "question_id": q_id,
                        "question": question,
                        "question_type": q_type,
                        "error_type": err_class,
                        "expected_pages": expected_pages,
                        "retrieved_pages": retrieved_pages_5,
                        "expected_chunks": expected_chunks,
                        "retrieved_chunks": reranked_top_5,
                        "vector_top_chunks": vector_top_5,
                    }
                )

            per_query_results.append(
                {
                    "id": q_id,
                    "question": question,
                    "question_type": q_type,
                    "difficulty": item.get("difficulty", "medium"),
                    "vector_mrr": v_mrr,
                    "reranked_mrr": r_mrr,
                    "vector_latency_ms": v_lat,
                    "rerank_latency_ms": r_lat,
                    "total_latency_ms": tot_lat,
                    "error_classification": err_class,
                }
            )

        # Aggregate metrics
        avg_vec_mrr = round(statistics.mean(vector_mrrs), 4) if vector_mrrs else 0.0
        avg_rerank_mrr = round(statistics.mean(reranked_mrrs), 4) if reranked_mrrs else 0.0

        vec_k_summary = {}
        rerank_k_summary = {}

        for k in k_list:
            v_p = round(statistics.mean(vec_k_accum[k]["precision"]), 4) if vec_k_accum[k]["precision"] else 0.0
            v_r = round(statistics.mean(vec_k_accum[k]["recall"]), 4) if vec_k_accum[k]["recall"] else 0.0
            v_h = round(statistics.mean(vec_k_accum[k]["hit_rate"]), 4) if vec_k_accum[k]["hit_rate"] else 0.0
            v_ph = round(statistics.mean(vec_k_accum[k]["page_hit"]), 4) if vec_k_accum[k]["page_hit"] else 0.0
            v_dh = round(statistics.mean(vec_k_accum[k]["doc_hit"]), 4) if vec_k_accum[k]["doc_hit"] else 0.0

            r_p = round(statistics.mean(rerank_k_accum[k]["precision"]), 4) if rerank_k_accum[k]["precision"] else 0.0
            r_r = round(statistics.mean(rerank_k_accum[k]["recall"]), 4) if rerank_k_accum[k]["recall"] else 0.0
            r_h = round(statistics.mean(rerank_k_accum[k]["hit_rate"]), 4) if rerank_k_accum[k]["hit_rate"] else 0.0
            r_ph = round(statistics.mean(rerank_k_accum[k]["page_hit"]), 4) if rerank_k_accum[k]["page_hit"] else 0.0
            r_dh = round(statistics.mean(rerank_k_accum[k]["doc_hit"]), 4) if rerank_k_accum[k]["doc_hit"] else 0.0

            vec_k_summary[f"K={k}"] = {
                "precision": v_p,
                "recall": v_r,
                "hit_rate": v_h,
                "page_hit_rate": v_ph,
                "doc_hit_rate": v_dh,
            }
            rerank_k_summary[f"K={k}"] = {
                "precision": r_p,
                "recall": r_r,
                "hit_rate": r_h,
                "page_hit_rate": r_ph,
                "doc_hit_rate": r_dh,
            }

        # Calculate Relative Improvements
        improvements = [
            {
                "metric": "MRR",
                "baseline": avg_vec_mrr,
                "reranked": avg_rerank_mrr,
                "improvement_percentage": calculate_improvement_percentage(avg_vec_mrr, avg_rerank_mrr),
            },
            {
                "metric": "Precision@5",
                "baseline": vec_k_summary["K=5"]["precision"],
                "reranked": rerank_k_summary["K=5"]["precision"],
                "improvement_percentage": calculate_improvement_percentage(
                    vec_k_summary["K=5"]["precision"], rerank_k_summary["K=5"]["precision"]
                ),
            },
            {
                "metric": "Recall@5",
                "baseline": vec_k_summary["K=5"]["recall"],
                "reranked": rerank_k_summary["K=5"]["recall"],
                "improvement_percentage": calculate_improvement_percentage(
                    vec_k_summary["K=5"]["recall"], rerank_k_summary["K=5"]["recall"]
                ),
            },
            {
                "metric": "Hit Rate@5",
                "baseline": vec_k_summary["K=5"]["hit_rate"],
                "reranked": rerank_k_summary["K=5"]["hit_rate"],
                "improvement_percentage": calculate_improvement_percentage(
                    vec_k_summary["K=5"]["hit_rate"], rerank_k_summary["K=5"]["hit_rate"]
                ),
            },
            {
                "metric": "Page Hit Rate@5",
                "baseline": vec_k_summary["K=5"]["page_hit_rate"],
                "reranked": rerank_k_summary["K=5"]["page_hit_rate"],
                "improvement_percentage": calculate_improvement_percentage(
                    vec_k_summary["K=5"]["page_hit_rate"], rerank_k_summary["K=5"]["page_hit_rate"]
                ),
            },
        ]

        # Latency statistics
        v_lat_stats = compute_statistical_summary(vector_latencies)
        r_lat_stats = compute_statistical_summary(rerank_latencies)
        tot_lat_stats = compute_statistical_summary(total_latencies)

        unanswerable_total = sum(1 for item in dataset if item.get("question_type") == "unanswerable")
        abstention_successes = error_classifications.get("unanswerable_abstention_success", 0)
        abstention_acc = (
            round(abstention_successes / unanswerable_total, 4) if unanswerable_total > 0 else 1.0
        )

        # Breakdown of MRR by question type
        by_type_summary = {}
        for q_t, scores in by_type_mrr.items():
            by_type_summary[q_t] = {
                "count": len(scores["vector"]),
                "vector_mrr": round(statistics.mean(scores["vector"]), 4),
                "reranked_mrr": round(statistics.mean(scores["reranked"]), 4),
                "mrr_improvement_pct": calculate_improvement_percentage(
                    statistics.mean(scores["vector"]), statistics.mean(scores["reranked"])
                ),
            }

        # Build full summary dictionary
        summary_result = {
            "experiment_id": exp_id,
            "timestamp": now_utc.isoformat(),
            "dataset_version": dataset_version,
            "questions_evaluated": len(dataset),
            "configuration": {
                "candidate_k": candidate_k,
                "k_values": k_list,
                "embedding_model": settings.EMBEDDING_MODEL,
                "reranker_model": settings.RERANKER_MODEL,
                "collection_name": self.collection_name,
            },
            "baseline_vector": {
                "method_name": "Vector Retrieval Only",
                "reranking_enabled": False,
                "metrics_by_k": vec_k_summary,
                "mrr": avg_vec_mrr,
                "abstention_accuracy": abstention_acc,
                "avg_retrieval_latency_ms": v_lat_stats["mean"],
                "avg_rerank_latency_ms": 0.0,
                "avg_total_latency_ms": v_lat_stats["mean"],
            },
            "enhanced_reranked": {
                "method_name": "Vector + Cross-Encoder Reranking",
                "reranking_enabled": True,
                "metrics_by_k": rerank_k_summary,
                "mrr": avg_rerank_mrr,
                "abstention_accuracy": abstention_acc,
                "avg_retrieval_latency_ms": v_lat_stats["mean"],
                "avg_rerank_latency_ms": r_lat_stats["mean"],
                "avg_total_latency_ms": tot_lat_stats["mean"],
            },
            "improvements": improvements,
            "latency_statistics": {
                "vector_search": v_lat_stats,
                "cross_encoder_rerank": r_lat_stats,
                "total": tot_lat_stats,
            },
            "by_question_type": by_type_summary,
            "error_summary": error_classifications,
        }

        # Save artifacts
        summary_path = RESULTS_DIR / f"{exp_id}_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_result, f, indent=2)

        # Save query-level results
        queries_path = RESULTS_DIR / f"{exp_id}_queries.json"
        with open(queries_path, "w", encoding="utf-8") as f:
            json.dump(per_query_results, f, indent=2)

        # Save error analysis report
        error_report_path = REPORTS_DIR / f"{exp_id}_error_analysis.json"
        error_data = {
            "experiment_id": exp_id,
            "timestamp": now_utc.isoformat(),
            "error_counts": error_classifications,
            "detailed_failures": detailed_error_reports,
        }
        with open(error_report_path, "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2)

        # Standard canonical summary and reports updated when evaluating full dataset
        if limit is None or limit >= 50:
            canonical_summary_path = RESULTS_DIR / "summary.json"
            with open(canonical_summary_path, "w", encoding="utf-8") as f:
                json.dump(summary_result, f, indent=2)

            canonical_error_path = REPORTS_DIR / "error_analysis.json"
            with open(canonical_error_path, "w", encoding="utf-8") as f:
                json.dump(error_data, f, indent=2)

        logger.info(
            "Benchmark completed. MRR: Vector=%.4f, Reranked=%.4f (Gain: %+.2f%%). Results saved to %s",
            avg_vec_mrr,
            avg_rerank_mrr,
            calculate_improvement_percentage(avg_vec_mrr, avg_rerank_mrr),
            summary_path,
        )

        return summary_result
