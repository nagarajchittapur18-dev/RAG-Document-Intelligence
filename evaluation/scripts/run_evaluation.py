"""
Standalone Command-Line Academic Evaluation Runner for DocuRAG / RAGMate Phase 12.
Validates dataset, runs dual-configuration evaluation, calculates full IR metrics,
profiles latency, performs error analysis, and exports academic tables and markdown reports.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure backend and root app imports are available
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir))

from app.services.evaluation_engine import EvaluationEngine
from evaluation.scripts.validate_dataset import DatasetValidator

RESULTS_DIR = root_dir / "evaluation" / "results"
REPORTS_DIR = root_dir / "evaluation" / "reports"


def format_markdown_report(summary: Dict[str, Any]) -> str:
    """Formats the benchmark summary into an academic research report."""
    exp_id = summary["experiment_id"]
    timestamp = summary["timestamp"]
    q_count = summary["questions_evaluated"]
    vec = summary["baseline_vector"]
    rerank = summary["enhanced_reranked"]
    lat = summary["latency_statistics"]
    by_type = summary.get("by_question_type", {})
    errs = summary["error_summary"]

    lines = [
        f"# DocuRAG Academic Research Evaluation Report",
        f"**Experiment ID:** `{exp_id}`  ",
        f"**Timestamp (UTC):** {timestamp}  ",
        f"**Questions Evaluated:** {q_count}  ",
        f"**Embedding Model:** `{summary['configuration']['embedding_model']}`  ",
        f"**Reranker Model:** `{summary['configuration']['reranker_model']}`  ",
        "",
        "---",
        "",
        "## 1. Primary Retrieval Performance Comparison",
        "",
        "| Evaluation Metric | Baseline: Vector-Only | Enhanced: Vector + Reranking | Relative Improvement |",
        "|---|---:|---:|---:|",
    ]

    for imp in summary["improvements"]:
        metric = imp["metric"]
        b_val = imp["baseline"]
        r_val = imp["reranked"]
        pct = imp["improvement_percentage"]
        sign = "+" if pct > 0 else ""
        lines.append(f"| **{metric}** | {b_val:.4f} | {r_val:.4f} | **{sign}{pct:.2f}%** |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Granular Cutoff Performance (K = 1, 3, 5, 10)",
        "",
        "| Cutoff K | Vector Precision | Reranked Precision | Vector Recall | Reranked Recall | Vector Hit Rate | Reranked Hit Rate |",
        "|:---|---:|---:|---:|---:|---:|---:|",
    ])

    for k_key in ["K=1", "K=3", "K=5", "K=10"]:
        if k_key in vec["metrics_by_k"] and k_key in rerank["metrics_by_k"]:
            vk = vec["metrics_by_k"][k_key]
            rk = rerank["metrics_by_k"][k_key]
            lines.append(
                f"| **{k_key}** | {vk['precision']:.4f} | {rk['precision']:.4f} | "
                f"{vk['recall']:.4f} | {rk['recall']:.4f} | {vk['hit_rate']:.4f} | {rk['hit_rate']:.4f} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## 3. End-to-End Latency Benchmark (ms)",
        "",
        "| Pipeline Stage | Mean (ms) | Median (ms) | Min (ms) | Max (ms) | Std Dev (ms) |",
        "|---|---:|---:|---:|---:|---:|",
        f"| **Vector Search (ChromaDB)** | {lat['vector_search']['mean']:.2f} | {lat['vector_search']['median']:.2f} | {lat['vector_search']['min']:.2f} | {lat['vector_search']['max']:.2f} | {lat['vector_search']['std_dev']:.2f} |",
        f"| **Cross-Encoder Rerank (CPU)** | {lat['cross_encoder_rerank']['mean']:.2f} | {lat['cross_encoder_rerank']['median']:.2f} | {lat['cross_encoder_rerank']['min']:.2f} | {lat['cross_encoder_rerank']['max']:.2f} | {lat['cross_encoder_rerank']['std_dev']:.2f} |",
        f"| **Combined Retrieval Pipeline** | {lat['total']['mean']:.2f} | {lat['total']['median']:.2f} | {lat['total']['min']:.2f} | {lat['total']['max']:.2f} | {lat['total']['std_dev']:.2f} |",
        "",
        "---",
        "",
        "## 4. Performance Breakdown by Question Type",
        "",
        "| Question Type | Sample Count | Vector MRR | Reranked MRR | Relative Gain |",
        "|---|---:|---:|---:|---:|",
    ])

    for q_t, t_data in by_type.items():
        v_mrr = t_data["vector_mrr"]
        r_mrr = t_data["reranked_mrr"]
        pct = t_data["mrr_improvement_pct"]
        sign = "+" if pct > 0 else ""
        lines.append(f"| `{q_t}` | {t_data['count']} | {v_mrr:.4f} | {r_mrr:.4f} | {sign}{pct:.2f}% |")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Error & Failure Analysis Classification",
        "",
        "| Classification Outcome | Count | Description |",
        "|---|---:|---|",
        f"| **Success (Target in Top-5)** | {errs.get('success', 0)} | Expected evidence chunk retrieved within Top-5 reranked set. |",
        f"| **Unanswerable Abstention Success** | {errs.get('unanswerable_abstention_success', 0)} | System correctly recognized out-of-domain query and triggered refusal. |",
        f"| **Reranking Failure** | {errs.get('reranking_failure', 0)} | Target chunk retrieved by vector search but demoted below Top-5 by cross-encoder. |",
        f"| **Retrieval Failure** | {errs.get('retrieval_failure', 0)} | Target chunk not captured in initial bi-encoder candidate pool (N=15). |",
        f"| **Page Mismatch** | {errs.get('page_mismatch', 0)} | Target document located, but wrong page was selected in top ranks. |",
        f"| **Abstention Failure** | {errs.get('abstention_failure', 0)} | System attempted to answer an unanswerable query without sufficient grounding. |",
        "",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run DocuRAG Academic Evaluation")
    parser.add_argument("--candidate-k", type=int, default=15, help="First-stage candidate pool size (default: 15)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of evaluation questions (default: all)")
    parser.add_argument("--no-validate", action="store_true", help="Skip dataset validation check")
    args = parser.parse_args()

    print("=" * 75)
    print("  PHASE 12: DOCURAG QUANTITATIVE ACADEMIC EVALUATION")
    print("=" * 75)

    # 1. Dataset Validation
    if not args.no_validate:
        print("\n[Step 1/3] Validating Evaluation Dataset Schema & Chunk Integrity...")
        validator = DatasetValidator()
        v_res = validator.validate()
        if not v_res["is_valid"]:
            print(f"Validation failed with {len(v_res['errors'])} errors! Aborting evaluation.")
            for err in v_res["errors"][:10]:
                print(f" - {err}")
            sys.exit(1)
        print(f" -> Validation successful: {v_res['total_questions']} verified questions.")
    else:
        print("\n[Step 1/3] Skipping dataset validation (--no-validate flag).")

    # 2. Run Benchmark
    print(f"\n[Step 2/3] Executing Quantitative Evaluation Benchmark...")
    print(f" -> Candidate Pool K: {args.candidate_k}")
    print(f" -> Cutoff K Values:  [1, 3, 5, 10]")

    engine = EvaluationEngine()
    summary = engine.run_benchmark(candidate_k=args.candidate_k, limit=args.limit)

    # 3. Export & Display Report
    print("\n[Step 3/3] Generating Academic Reports & Tables...")
    report_md = format_markdown_report(summary)
    
    report_path = REPORTS_DIR / f"{summary['experiment_id']}_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    canonical_report_path = REPORTS_DIR / "evaluation_report.md"
    with open(canonical_report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print("\n" + report_md)
    print("\n" + "=" * 75)
    print(f"  EVALUATION COMPLETE!")
    print(f"  Summary Artifact: {summary['experiment_id']}_summary.json")
    print(f"  Markdown Report:  {report_path}")
    print("=" * 75)


if __name__ == "__main__":
    main()
