# DocuRAG Academic Research Evaluation Report
**Experiment ID:** `EXP_20261004_065505_60`  
**Timestamp (UTC):** 2026-10-04T06:55:05.024389+00:00  
**Questions Evaluated:** 60  
**Embedding Model:** `all-MiniLM-L6-v2`  
**Reranker Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2`  

---

## 1. Primary Retrieval Performance Comparison

| Evaluation Metric | Baseline: Vector-Only | Enhanced: Vector + Reranking | Relative Improvement |
|---|---:|---:|---:|
| **MRR** | 0.9228 | 0.9188 | **-0.43%** |
| **Precision@5** | 0.2481 | 0.2630 | **+6.01%** |
| **Recall@5** | 0.9506 | 0.9938 | **+4.54%** |
| **Hit Rate@5** | 0.9815 | 1.0000 | **+1.88%** |
| **Page Hit Rate@5** | 0.9815 | 1.0000 | **+1.88%** |

---

## 2. Granular Cutoff Performance (K = 1, 3, 5, 10)

| Cutoff K | Vector Precision | Reranked Precision | Vector Recall | Reranked Recall | Vector Hit Rate | Reranked Hit Rate |
|:---|---:|---:|---:|---:|---:|---:|
| **K=1** | 0.8704 | 0.8704 | 0.7500 | 0.7407 | 0.8704 | 0.8704 |
| **K=3** | 0.3950 | 0.4136 | 0.9290 | 0.9414 | 0.9815 | 0.9630 |
| **K=5** | 0.2481 | 0.2630 | 0.9506 | 0.9938 | 0.9815 | 1.0000 |
| **K=10** | 0.1296 | 0.1315 | 0.9846 | 0.9938 | 1.0000 | 1.0000 |

---

## 3. End-to-End Latency Benchmark (ms)

| Pipeline Stage | Mean (ms) | Median (ms) | Min (ms) | Max (ms) | Std Dev (ms) |
|---|---:|---:|---:|---:|---:|
| **Vector Search (ChromaDB)** | 13.28 | 12.82 | 10.02 | 18.98 | 1.89 |
| **Cross-Encoder Rerank (CPU)** | 232.50 | 133.00 | 109.16 | 5059.68 | 635.94 |
| **Combined Retrieval Pipeline** | 245.78 | 143.78 | 121.97 | 5078.66 | 636.71 |

---

## 4. Performance Breakdown by Question Type

| Question Type | Sample Count | Vector MRR | Reranked MRR | Relative Gain |
|---|---:|---:|---:|---:|
| `fact` | 12 | 0.9028 | 0.8361 | -7.38% |
| `methodology` | 8 | 1.0000 | 0.9167 | -8.33% |
| `algorithm` | 8 | 0.8333 | 0.9062 | +8.75% |
| `results` | 8 | 1.0000 | 1.0000 | 0.00% |
| `comparison` | 8 | 0.8542 | 0.9375 | +9.76% |
| `multi_hop` | 6 | 0.9167 | 0.9167 | 0.00% |
| `contextual` | 4 | 1.0000 | 1.0000 | 0.00% |

---

## 5. Error & Failure Analysis Classification

| Classification Outcome | Count | Description |
|---|---:|---|
| **Success (Target in Top-5)** | 54 | Expected evidence chunk retrieved within Top-5 reranked set. |
| **Unanswerable Abstention Success** | 6 | System correctly recognized out-of-domain query and triggered refusal. |
| **Reranking Failure** | 0 | Target chunk retrieved by vector search but demoted below Top-5 by cross-encoder. |
| **Retrieval Failure** | 0 | Target chunk not captured in initial bi-encoder candidate pool (N=15). |
| **Page Mismatch** | 0 | Target document located, but wrong page was selected in top ranks. |
| **Abstention Failure** | 0 | System attempted to answer an unanswerable query without sufficient grounding. |
