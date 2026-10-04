# DocuRAG — Final MCA Viva Voce Quick-Reference Cheat Sheet
**Academic Title:** *AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation*  
**Format:** High-Density 2–3 Page Rapid Revision Sheet for Examination Day  

---

## 1. Core System Definitions (One-Liners)

- **Project Definition**: **DocuRAG** is an enterprise-grade multi-tenant platform for intelligent document question answering that eliminates LLM hallucinations on private PDFs through two-stage retrieval and deterministic citation verification.
- **Architecture Flow**: React 18 SPA $\rightarrow$ FastAPI Gateway (JWT) $\rightarrow$ PyMuPDF Chunker $\rightarrow$ ChromaDB HNSW Search ($M=15$) $\rightarrow$ Cross-Encoder Re-ranker ($K=5$) $\rightarrow$ Gemini 2.5 Flash $\rightarrow$ Citation Sanitizer $\rightarrow$ Interactive Evidence Drawer.
- **RAG (Retrieval-Augmented Generation)**: An AI paradigm that retrieves factual external text passages at query time and injects them into an LLM's prompt context to produce grounded, verifiable answers without retraining model weights.
- **Embeddings**: Dense 384-dimensional continuous numerical vectors produced by `all-MiniLM-L6-v2` that project semantic textual meanings into geometric space where cosine similarity equals the inner dot product.
- **ChromaDB**: An open-source, AI-native vector database implementing the Hierarchical Navigable Small World (HNSW) graph algorithm for sub-linear ($O(\log N)$) approximate nearest neighbor cosine similarity search with tenant metadata filtering.
- **Cross-Encoder Re-Ranking**: A deep transformer model (`ms-marco-MiniLM-L-6-v2`) that evaluates query-passage pairs simultaneously using full joint token cross-attention, capturing nuanced token interactions missed by independent bi-encoders.
- **Google Gemini 2.5 Flash**: A low-latency multimodal LLM queried strictly on the backend with temperature 0.2 to synthesize natural language answers conditioned exclusively on delimited document evidence.
- **Citation Sanitizer**: An algorithmic regex post-processor that verifies generated citation markers (`[1]`, `[2]`), prunes out-of-bounds indices, and extracts exact source snippets and page links for the UI Evidence Drawer.

---

## 2. Key Architecture Numbers & Invariants (Must Memorize)

| Parameter | Exact Value | Technical Rationale |
|---|:---:|---|
| **Chunk Size ($C_{\max}$)** | **500 tokens** (~2,000 chars) | Fits inside embedding context while preserving paragraph coherence |
| **Chunk Overlap ($O$)** | **100 tokens** (~400 chars) | Prevents semantic truncation of sentences straddling boundaries |
| **Embedding Dimension ($d$)** | **384 dimensions** | Standard dimension for `sentence-transformers/all-MiniLM-L6-v2` |
| **Vector Normalization** | **$L_2$-norm ($\|\mathbf{v}\|_2 = 1.0$)** | Reduces cosine distance calculation to fast dot product $\hat{\mathbf{q}} \cdot \hat{\mathbf{v}}$ |
| **Candidate Pool Size ($M$)** | **15 chunks** | Over-fetched in Stage 1 to guarantee high candidate recall |
| **Final Context Size ($Top-K$)** | **5 chunks** | Filtered by re-ranker ($\sigma_i \ge 0.15$) for prompt context |
| **Gemini Hyperparameters** | **Temp = 0.2, Top_P = 0.95** | Forces deterministic, factual output and suppresses creativity |
| **Rate Limit** | **60 req/min per IP** | Sliding-window in-memory protection against API abuse |
| **Total Automated Tests** | **119 / 119 Passing** | 100% pass rate across 17 test modules in 56.86 seconds |
| **Frontend Bundle Size** | **245.6 kB gzipped** | Production Vite build transformed 2,562 modules in 1.90s |

---

## 3. Actual Empirical Results Table (Experiment `EXP_20261004_065505_60`)

*Tested across 24-page academic corpus (72 chunks) and 60 Cranfield benchmark questions.*

| Metric | Stage 1: Vector Search | Stage 2: Cross-Encoder Reranked | Delta Gain | What to Say in Viva |
|---|:---:|:---:|:---:|---|
| **Precision@5** | 0.2481 | **0.2630** | **+6.01%** | Operates at the theoretical maximum ceiling ($\approx 1.3/5$) |
| **Recall@5** | 0.9506 | **0.9938** | **+4.54%** | Captures 99.38% of all possible evidence in the top 5 chunks |
| **Hit Rate@5** | 0.9815 | **1.0000** | **+1.89%** | **Flawless 100% coverage** (0 questions missed relevant evidence) |
| **Hit Rate@10** | 0.9815 | **1.0000** | **+1.89%** | Total coverage maintained at $K = 10$ |
| **Overall MRR** | **0.9228** | 0.9188 | -0.43% | Stable across all 60 queries; factoids favor bi-encoders |
| **Comparison MRR** | 0.8500 | **0.9333** | **+9.76%** | **Massive gain** due to cross-attention & document balancing |
| **Algorithm MRR** | 0.8750 | **0.9500** | **+8.75%** | Resolves complex structural and mathematical procedures |
| **Abstention Accuracy**| **1.0000** | **1.0000** | **0.00%** | **100% Safe Refusal** on all 6 out-of-domain unanswerable queries |

### Latency Profiles (Median on CPU):
- Vector Search: **12.82 ms** | Re-Ranking: **133.00 ms** | Gemini Synthesis: **1,310.00 ms** | Total System Roundtrip: **1,455.82 ms** (~1.46s).

---

## 4. Security Mechanisms (5 Pillars)
1. **Multi-Tenant Isolation**: Every database table and ChromaDB query is scoped strictly to authenticated `user_id`.
2. **IDOR Neutralization**: Attempting to query or delete an unowned document or chat session returns HTTP 404/403.
3. **Input & File Hardening**: Extension whitelisting (`.pdf`), magic byte verification, path traversal scrubbing, and 30 MB size limits.
4. **Indirect Prompt Injection Defense**: Document text is isolated between XML delimiters and explicitly marked as UNTRUSTED DATA.
5. **SQL Injection Defense**: 100% parameterized queries via SQLAlchemy ORM; passwords hashed with salted bcrypt (cost 12).

---

## 5. Deployment Topology (Multi-Cloud)
- **Frontend SPA**: Hosted on **Vercel Edge CDN** (React 18, Vite, Tailwind CSS, SPA rewrites `/* -> /index.html 200`).
- **Backend API**: Hosted on **Render** (FastAPI, Uvicorn ASGI, 4 worker threads, Docker containerized).
- **Relational Database**: Hosted on **Neon Serverless PostgreSQL** (SQLAlchemy connection pool `pool_size=10`, SSL mode).
- **File Storage**: Pluggable `BaseStorageProvider` supporting local disk and **AWS S3** (`boto3`).
- **Vector Database**: Persistent **ChromaDB** volume or remote `HttpClient`.

---

## 6. Top 5 System Limitations (Be Honest & Academic)
1. **CPU Re-ranking Latency Scaling**: Cross-encoder latency scales linearly with candidate pool size ($M$); candidate pools are bounded to $\le 20$ on CPU hardware.
2. **Dual-Model Memory Footprint**: Keeping both `all-MiniLM-L6-v2` and `ms-marco-MiniLM-L-6-v2` in RAM requires ~450 MB resident memory.
3. **Single-Hop Query Scope**: Does not support autonomous multi-hop iterative sub-queries across disjoint sections.
4. **Scanned PDF Support**: Rejects image-only scanned PDFs without embedded OCR text layers (`ScannedPDFError`).
5. **Unmeasured LLM-as-a-Judge**: Evaluated via Cranfield IR standards; automated LLM faithfulness scoring was not measured in this setup.

---

## 7. Top 5 Future Enhancements
1. **ColBERT Token Late Interaction**: Implement MaxSim token scoring to get cross-encoder precision at bi-encoder speeds.
2. **Graph-RAG Knowledge Fusion**: Construct entity-relationship graphs to enable multi-hop reasoning across documents.
3. **Domain Cross-Encoder Fine-Tuning**: Fine-tune cross-encoders on legal and medical corpora using contrastive margin MSE loss.
4. **Agentic RAG State Machines**: Implement iterative query decomposition and reflection loops using LangGraph.
5. **Integrated OCR Ingestion**: Add embedded Tesseract/PaddleOCR for automatic image-based PDF digitization.
