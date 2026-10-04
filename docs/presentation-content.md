# DocuRAG — Final MCA Project Presentation Slides Content
**Academic Title:** *AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation*  
**Format:** 20 Professional Slides for Master of Computer Applications Viva Voce Defense  

---

### Slide 1: Title & Candidacy
- **Project Title:** DocuRAG: AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation
- **Candidate Name:** [STUDENT NAME] (USN: [USN])
- **Internal Guide:** [GUIDE NAME], [Designation]
- **Department:** Department of Computer Applications, [College Name]
- **Academic Year:** 2025–2026

---

### Slide 2: Introduction to Document QA & LLMs
- Large Language Models (LLMs) excel at language understanding, summarization, and reasoning.
- However, enterprise knowledge lives inside private, unstructured documents (PDFs, contracts, specifications).
- Fine-tuning models on organizational documents is slow, cost-prohibitive, and causes catastrophic forgetting.
- Retrieval-Augmented Generation (RAG) decouples parametric reasoning from dynamic external knowledge.
- DocuRAG provides an enterprise-ready, auditable, and hallucination-resistant document QA solution.

---

### Slide 3: Problem Statement
- Standard LLMs suffer from **parametric cutoffs** and have no access to uploaded PDF documents.
- Under ambiguity, autoregressive models generate plausible, fluent, but factually fabricated statements (**hallucinations**).
- Traditional search tools lack semantic understanding; naive single-stage RAG systems suffer from representation bottlenecks and vocabulary mismatch.
- Models fail to provide verifiable source citations, making factual audit impossible in critical domains.

---

### Slide 4: Motivation & Industry Context
- **Need for Verification**: High-stakes domains (legal, medical, academic, financial) demand 100% verifiable answers.
- **Auditable AI**: Every assertion must link directly to the exact source page and paragraph.
- **Enterprise Multi-Tenancy**: Organizations require strict user isolation where users query private documents without data leakage.
- **Efficiency**: Running complex cross-encoders across millions of documents is computationally intractable; a hybrid two-stage coarse-to-fine architecture is essential.

---

### Slide 5: Existing Systems Analysis
- **Lexical Keyword Search (BM25 / Elasticsearch)**: Fast exact-match capability, but fails completely on synonyms, paraphrasing, and conceptual queries (term mismatch).
- **Standalone LLM Direct Querying**: Subject to token context limits, high per-call cost, and severe parametric hallucination.
- **Naive Single-Stage RAG Systems**:
  - Independent bi-encoder vector cosine similarity misses nuanced token interactions.
  - Document starvation: verbose documents crowd out relevant evidence from shorter documents.
  - Unverified citations: models hallucinate fake page numbers.

---

### Slide 6: Research Gap
1. **Vector Representation Bottleneck**: Forcing 500 tokens into a single 384-d vector loses relational details between entities.
2. **"Lost-in-the-Middle" Phenomenon**: Decoder LLMs struggle to attend to evidence located in the middle of long prompts.
3. **Absence of Fair Multi-Document Sampling**: Existing vector databases lack metadata-aware partitioning for comparative queries.
4. **Lack of Algorithmic Citation Verification**: Most systems rely on LLM honesty, lacking post-generation verification to catch fabricated citations.

---

### Slide 7: Project Objectives
1. Build an asynchronous, multi-tenant document ingestion pipeline for multi-page PDFs with layout-aware text sanitization.
2. Construct a **two-stage coarse-to-fine retrieval engine** combining bi-encoder vector search with cross-encoder joint token re-ranking.
3. Formulate an **adaptive document-balancing algorithm** to guarantee fair representation in multi-document queries.
4. Engineer a **deterministic citation verification engine** providing clickable inline markers and an interactive Evidence Drawer.
5. Scientifically evaluate the system using a **60-question Cranfield benchmark** across a 24-page academic corpus.
6. Validate through **119 automated tests** (100% pass rate) and deploy to a multi-cloud production architecture.

---

### Slide 8: Proposed System: DocuRAG
- **Client Tier**: React 18 SPA featuring an interactive Evidence Drawer, chat history, and visual PDF page previews.
- **API Gateway Tier**: FastAPI with JWT multi-tenant isolation, sliding-window rate limiting, and request tracing.
- **Two-Stage Retrieval Engine**:
  - *Stage 1*: ChromaDB HNSW vector search over-fetches $M = 15$ candidates.
  - *Stage 2*: Cross-encoder (`ms-marco-MiniLM-L-6-v2`) re-ranks candidates to select the top-$K = 5$ chunks.
- **Grounded Generation Engine**: Google Gemini 2.5 Flash operating under strict anti-jailbreak prompt delimiters with algorithmic citation sanitization.

---

### Slide 9: High-Level System Architecture
```text
React 18 Frontend  <─── HTTPS / JWT ───>  FastAPI Gateway (Uvicorn)
                                                    │
                   ┌────────────────────────────────┼────────────────────────────────┐
                   ▼                                ▼                                ▼
         PyMuPDF Ingestion               Two-Stage RAG Engine            Relational Persistence
       (Text/Page Extraction)          (ChromaDB + CrossEncoder)        (PostgreSQL / SQLAlchemy)
                   │                                │                                │
                   ▼                                ▼                                ▼
         Recursive Chunker                Google Gemini 2.5 Flash         JWT Multi-Tenant State
        (500-token / 100-overlap)       (Grounded Answer + Citations)    (Users, Sessions, Messages)
```

---

### Slide 10: The Complete RAG Execution Pipeline
1. **Ingest**: PDF $\rightarrow$ PyMuPDF $\rightarrow$ Clean $\rightarrow$ 500-token chunks with 100-token overlap.
2. **Embed**: Chunks $\rightarrow$ `all-MiniLM-L6-v2` $\rightarrow$ 384-d normalized vectors $\rightarrow$ ChromaDB HNSW.
3. **Query**: User query $\rightarrow$ Contextual pronoun rewrite $\rightarrow$ 384-d vector.
4. **Stage 1 Retrieval**: ChromaDB HNSW search retrieves candidate pool $M = 15$.
5. **Fair Balance**: Adaptive quota allocation ($\lfloor K / T \rfloor$) across active documents.
6. **Stage 2 Re-ranking**: Cross-encoder joint attention re-ranks candidates $\rightarrow$ Top $K = 5$.
7. **Synthesis**: Delimited context envelope $\rightarrow$ Gemini 2.5 Flash $\rightarrow$ Inline citations `[1]`, `[2]`.
8. **Sanitize & Deliver**: Out-of-bounds citations pruned $\rightarrow$ Evidence Drawer populated with snippets and page views.

---

### Slide 11: Technology Stack
- **Frontend**: React 18, Vite 8, Tailwind CSS, Lucide Icons, Chart.js.
- **Backend**: FastAPI 0.115, Uvicorn, Python 3.10+, Pydantic v2.
- **NLP & AI**: PyMuPDF (`fitz`), `sentence-transformers/all-MiniLM-L6-v2`, `cross-encoder/ms-marco-MiniLM-L-6-v2`, Google Gemini 2.5 Flash API.
- **Databases**: ChromaDB 0.5 (Vector HNSW), PostgreSQL 15 / SQLite 3 (SQLAlchemy ORM).
- **Security & Quality**: Bcrypt, Python-Jose (JWT), Pytest (119 tests passing).
- **Deployment**: Vercel (Frontend SPA), Render (Backend API), Neon (Serverless Postgres), AWS S3 (Storage).

---

### Slide 12: Ingestion & Preprocessing Subsystem
- **PDF Extraction**: PyMuPDF layout extraction tracking 1-indexed pages.
- **Robust Exception Handling**:
  - Rejection of encrypted/password-protected PDFs (`CorruptPDFError`).
  - Detection of scanned image-only PDFs with no text layer (`ScannedPDFError`).
- **Text Normalization**: Reconnects broken hyphens, removes control characters, and standardizes whitespace.
- **Chunking Algorithm**: Recursive character splitting with separators `["\n\n", "\n", " ", ""]`. Max length = 500 tokens, overlap = 100 tokens. Each chunk preserves page number and character byte offsets.

---

### Slide 13: Two-Stage Retrieval & Neural Re-ranking
- **Stage 1 (Bi-Encoder Vector Search)**:
  - Vector dot-product equivalent to cosine similarity due to explicit $L_2$-normalization ($\|\mathbf{v}\|_2 = 1.0$).
  - Fast sub-linear $O(\log N)$ candidate over-fetching ($M = 15$ chunks in ~13 ms).
- **Stage 2 (Cross-Encoder Re-Ranking)**:
  - Full joint self-attention over sequence `[CLS] q [SEP] c_i [SEP]`.
  - Captures cross-token dependencies missed by vector dot products.
  - Scores normalized via sigmoid $\sigma_i = \frac{1}{1 + e^{-s_i}}$; noise threshold $\sigma_i \ge 0.15$.
  - Returns top $K = 5$ chunks in ~133 ms.

---

### Slide 14: Source Citations & Document Evidence
- **Strict Anti-Jailbreak System Prompt**: Delimited context envelopes instruct Gemini to rely *only* on context and ignore injected commands inside PDFs.
- **Citation Sanitization Engine**:
  - Regex parser extracts all citation indices.
  - Prunes out-of-bounds markers ($j > 5$ or $j \le 0$).
  - Remaps non-sequential markers sequentially.
- **Interactive UI Evidence Drawer**:
  - Displays 150-character highlighted evidence snippets.
  - Shows source document title, page number, vector score, and re-rank score.
  - On-demand single-page PDF rendering via `GET /api/documents/{id}/pages/{p}`.

---

### Slide 15: Experimental Evaluation Methodology
- **Cranfield IR Benchmark Paradigm**: Gold-standard empirical testing (`EXP_20261004_065505_60`).
- **24-Page Academic Corpus**:
  1. *Attention Is All You Need* (Vaswani et al., 2017) — 15 pages
  2. *Dense Passage Retrieval for Open-Domain QA* (Karpukhin et al., 2020) — 5 pages
  3. *Passage Re-ranking with BERT* (Nogueira & Cho, 2019) — 4 pages
- **60-Question Benchmark**: 54 answerable across Factoid, Concept, Comparison, Multi-Hop, Algorithm; 6 adversarial out-of-domain unanswerable queries.
- **Metrics Evaluated**: Precision@K, Recall@K, Hit Rate@K (for $K \in \{1, 3, 5, 10\}$), MRR, and Abstention Accuracy.

---

### Slide 16: Empirical Results & Comparative Analysis

| Metric | Stage 1 (Vector) | Stage 2 (Reranked) | Absolute Delta | Relative Gain |
|---|:---:|:---:|:---:|:---:|
| **Precision@5** | 0.2481 | **0.2630** | +0.0148 | **+6.01%** |
| **Recall@5** | 0.9506 | **0.9938** | +0.0432 | **+4.54%** |
| **Hit Rate@5** | 0.9815 | **1.0000** | +0.0185 | **+1.89% (100% Coverage)** |
| **Hit Rate@10** | 0.9815 | **1.0000** | +0.0185 | **+1.89% (100% Coverage)** |
| **Overall MRR** | **0.9228** | 0.9188 | -0.0040 | -0.43% |
| **Comparison MRR** | 0.8500 | **0.9333** | +0.0833 | **+9.76%** |
| **Algorithm MRR** | 0.8750 | **0.9500** | +0.0750 | **+8.75%** |
| **Abstention Accuracy** | **1.0000** | **1.0000** | 0.0000 | **100% Safe Refusal** |

- Re-ranking achieved a **flawless 100.0% Hit Rate@5** (zero missed questions).
- Complex comparison queries gained **+9.76% MRR**, validating adaptive document balancing.
- 100% safe refusal on all unanswerable queries eliminates hallucination.

---

### Slide 17: System Verification, Testing & Security
- **Comprehensive Test Suite**: **119 / 119 automated tests passing** across 17 test modules in 56.86 seconds.
- **Multi-Tenant Security**: Strict `user_id` verification prevents Insecure Direct Object References (IDOR).
- **Hardening Highlights**:
  - File upload MIME validation, extension whitelisting, and path traversal scrubbing.
  - SQL injection immunity via SQLAlchemy ORM parameterization.
  - Sliding-window rate limiting (60 req/min) and distributed request tracing (`X-Request-ID`).
- **Frontend Quality**: 0 linter errors across 35 React components; production build completed in 1.90s.

---

### Slide 18: Cloud Deployment & Infrastructure
- **Decoupled Multi-Cloud Architecture**:
  - *Frontend*: Vercel Edge CDN with SPA client rewrite rules.
  - *Backend*: Render Web Service (Uvicorn ASGI with 4 workers).
  - *Database*: Neon Serverless PostgreSQL with SQLAlchemy connection pool (`pool_size=10, max_overflow=20`).
  - *Storage*: Pluggable `BaseStorageProvider` supporting local disk and AWS S3 (`boto3`).
  - *Vector DB*: ChromaDB with persistent volume storage or remote `HttpClient`.
- **Health & Monitoring**: Kubernetes-compliant probes (`/health`, `/health/liveness`, `/health/readiness`).

---

### Slide 19: Limitations & Future Work
- **Identified Limitations**:
  - CPU cross-encoder latency scales linearly with candidate pool size ($M$).
  - Model memory footprint: dual in-memory models require ~450 MB resident RAM.
  - Single-hop retrieval: cannot autonomously decompose complex multi-hop queries.
  - Rejection of image-only scanned PDFs lacking text layers.
- **Future Enhancements**:
  - Domain-specific cross-encoder fine-tuning (legal/medical datasets).
  - ColBERT-style late-interaction token scoring (MaxSim operator).
  - Graph-RAG integration for entity-relationship knowledge graph traversals.
  - Integrated OCR engine (Tesseract/PaddleOCR) for scanned PDFs.

---

### Slide 20: Conclusion & Summary of Achievements
- Successfully designed, implemented, and empirically validated **DocuRAG**.
- Solved vector compression bottlenecks and vocabulary mismatch using two-stage neural re-ranking.
- Eliminated document starvation via adaptive multi-document fair balancing.
- Enforced 100% auditable evidence through deterministic citation sanitization and page previews.
- Achieved **100% Hit Rate@5**, **0.9938 Recall@5**, and **1.0000 Abstention Accuracy** with a median latency under 150 ms.
- Fully production-ready, passing 119 automated tests, with comprehensive MCA dissertation and IEEE research paper.

---

### Slide 21 (Bonus): Thank You & Viva Voce Q&A
- **Demonstration URL**: Live Application Dashboard
- **Source Code Repository**: Clean Git Master Branch (119/119 Tests Passing)
- **Open for Questions**: Thank you, respected examiners and faculty members.
