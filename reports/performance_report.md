# DocuRAG / RAGMate — Performance & Latency Report (Phase 14)
**Academic Title:** *AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation*  
**Date:** October 4, 2026  
**Environment:** Windows 11, Intel Core Multi-Core, Python 3.10.11, PyTorch CPU execution

---

## 1. System Performance Summary

| Pipeline Stage | Metric | Measured Value | SLA Target | Compliance |
|---|---|:---:|:---:|:---:|
| **PDF Text Extraction** | 10-page paper (PyMuPDF) | **148 ms** | < 1,000 ms | **PASS** |
| **Document Chunking** | 10-page paper (Recursive) | **36 ms** | < 500 ms | **PASS** |
| **Vector Search (ChromaDB)** | Median Latency | **12.82 ms** | < 50 ms | **PASS** |
| **Vector Search (ChromaDB)** | Mean Latency | **13.28 ms** | < 50 ms | **PASS** |
| **Cross-Encoder Reranking** | Warm Median Latency | **133.00 ms** | < 300 ms | **PASS** |
| **Cross-Encoder Reranking** | Mean Latency | **232.50 ms** | < 400 ms | **PASS** |
| **Total Retrieval Pipeline** | Median Latency | **143.78 ms** | < 500 ms | **PASS** |
| **Total Retrieval Pipeline** | p95 Latency | **218.40 ms** | < 600 ms | **PASS** |
| **Frontend Production Build** | Gzip JS Bundle | **245.61 kB** | < 500 kB | **PASS** |
| **Frontend Build Time** | Vite Production Build | **2.01 s** | < 15 s | **PASS** |

---

## 2. Ingestion & Preprocessing Benchmarks

Measurements performed across synthetic and gold corpus documents:

### A. Document Extraction & Cleaning Throughput
- **Engine:** PyMuPDF (`fitz`) with null-byte stripping, hyphenation reconstruction, and whitespace normalization.
- **10-page Academic Paper:**
  - Characters extracted: ~32,000
  - Extraction latency: **148.2 ms** (Throughput: ~67.5 pages/second).
- **24-page Academic Gold Corpus (3 PDFs):**
  - Total chunks generated: 24 chunks (avg. 1,000 characters per chunk, 150 char overlap).
  - Total chunking latency: **84.1 ms**.

### B. Batch Vector Embedding
- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors).
- **Execution Mode:** CPU batch encoding (`batch_size=32`).
- **Throughput:** ~42 chunks/second on standard CPU hardware.
- **Vector Normalization:** Strict L2 norm $\|\mathbf{v}\|_2 = 1.000 \pm 10^{-3}$, ensuring exact cosine distance mapping in ChromaDB.

---

## 3. Retrieval & Reranking Latency Profiling

Empirical latency breakdown measured across the 60 benchmark evaluation queries:

```text
End-to-End Retrieval Latency (Median: 143.78 ms)
┌─────────────────────────────────────────────────────────────┐
│  Vector Search (ChromaDB): 12.82 ms (8.9%)                  │
├─────────────────────────────────────────────────────────────┤
│  Cross-Encoder Reranker (ms-marco-MiniLM): 133.00 ms (91.1%)│
└─────────────────────────────────────────────────────────────┘
```

### Statistical Distribution

| Stage | Mean (ms) | Median (ms) | Min (ms) | Max (ms) | Std Dev (ms) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Stage 1: Vector Retrieval** | 13.28 | 12.82 | 10.02 | 18.98 | ±1.89 |
| **Stage 2: Cross-Encoder** | 232.50 | 133.00 | 109.16 | 5,059.68* | ±635.94 |
| **Total Retrieval Pipeline** | 245.78 | 143.78 | 121.97 | 5,078.66* | ±636.71 |

*\*Note on Maximum Latency (5,059 ms):* The observed maximum latency occurred on Query 1 and represents PyTorch cold-start model weight loading from disk into system memory. All subsequent warm inferences stabilized between 109 ms and 180 ms.

---

## 4. Context Optimization & Token Economy

To prevent context bloat, prompt token exhaustion, and API quota degradation:
1. **Candidate Pruning:** Bi-encoder fetches 15 initial candidates; Cross-Encoder prunes down to the top 5 most relevant chunks.
2. **Context Window Cap:** Enforced maximum of `MAX_CONTEXT_CHARS = 12000` (approximately 2,500 tokens), leaving sufficient headroom for Gemini's completion window.
3. **Conversation Memory Window:** Bounded to the most recent 10 turns (`CHAT_HISTORY_LIMIT = 10`), preventing unbounded memory accumulation in long-running sessions.
4. **Snippet Compression:** Evidence previews presented to the user are compressed to 300–500 character sentence-bounded excerpts (`extract_snippet`).

---

## 5. Memory & Model Singleton Verification

- **EmbeddingService:** Thread-safe singleton (`EmbeddingService._instance`). The 90 MB MiniLM weights are loaded exactly once into RAM during application startup.
- **RerankerService:** Thread-safe singleton (`RerankerService._instance`). The 80 MB Cross-Encoder weights are cached in memory, preventing repeated disk read cycles.
- **Garbage Collection:** Document file handles in PyMuPDF are enclosed in strict `try...finally: doc.close()` blocks, eliminating file descriptor leaks during continuous operation.
