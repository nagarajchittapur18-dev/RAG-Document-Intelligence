# DocuRAG / RAGMate: AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation (RAG)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Test Suite](https://img.shields.io/badge/Tests-113%2F113%20Passing-brightgreen.svg)]()

---

## 1. Project Title & Academic Overview
**AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation (RAG)**  
*Academic Degree / Level: Master of Computer Applications (MCA)*

---

## 2. Project Overview
**DocuRAG** (internal codename **RAGMate**) is an enterprise-ready, academically rigorous document question-answering platform built upon a multi-stage Retrieval-Augmented Generation (RAG) architecture. It enables users to upload PDF research papers, technical manuals, and business reports, automatically extracts and sanitizes page-by-page text, segments text into overlapping chunks while preserving provenance metadata, generates dense semantic embeddings in ChromaDB, applies cross-encoder neural reranking, and synthesizes hallucination-controlled answers with verified inline page citations using Google Gemini.

Additionally, DocuRAG features an integrated **Quantitative Evaluation Dashboard** that benchmarks Information Retrieval (IR) metrics ($P@K, R@K, \text{Hit Rate}@K, \text{MRR}$) and CPU inference latencies across a verified gold-standard academic dataset.

---

## 3. System Architecture
```mermaid
flowchart TD
    User([User / Browser])
    subgraph Frontend [React 19 + Vite + Tailwind CSS]
        UI[Dashboard / Chat / Doc Mgmt / Evaluation Dashboard]
        Router[React Router & Auth Context]
        EvidenceDrawer[Interactive Inline Citation & Evidence Drawer]
        Charts[Recharts Comparative IR Metrics & Latency Profiling]
    end

    subgraph Backend [FastAPI Backend]
        API[FastAPI Endpoints: Auth / Docs / Pages / Chat / Eval / Health]
        Auth[JWT & Bcrypt Security Layer]
        DB[(Relational DB: SQLite / PostgreSQL)]
        
        subgraph Pipeline [Document Ingestion Pipeline]
            PDFExtract[PyMuPDF Page-by-Page & Page-Serving Extractor]
            Cleaner[Text Sanitizer & Preprocessor]
            Chunker[Configurable Token/Char Chunker with Overlap]
            Embedder[SentenceTransformer all-MiniLM-L6-v2]
            Chroma[(ChromaDB Vector Store)]
        end
        
        subgraph RAG [Retrieval & Generation Engine]
            Retriever[Semantic Vector Retrieval]
            Rerank[Neural Cross-Encoder Reranker: ms-marco-MiniLM]
            PromptEngine[Hallucination-Controlled Grounding Prompt]
            Gemini[Google Gemini API]
            CitationGen[Deterministic Citation & Provenance Sanitizer]
        end

        subgraph AcademicEval [Research Evaluation Suite]
            EvalRunner[Automated Benchmark Runner & Engine]
            Corpus[(24-Page Multi-Doc Academic Corpus)]
            GoldDataset[(60 Verified Ground Truth Questions)]
            MetricsCalc[P@K, R@K, Hit Rate@K, MRR, Latency Profiler, Abstention Scorer]
        end
    end

    User <--> UI
    UI <--> Router
    UI <--> EvidenceDrawer
    UI <--> Charts
    Router <--> API
    API --> Auth --> DB
    API --> Pipeline
    Pipeline --> PDFExtract --> Cleaner --> Chunker --> Embedder --> Chroma
    API --> RAG
    RAG --> Retriever --> Chroma
    Retriever --> Rerank --> PromptEngine --> Gemini --> CitationGen --> API
    API --> AcademicEval
    AcademicEval --> Corpus & GoldDataset --> EvalRunner --> MetricsCalc
```

---

## 4. Key Features
- **Multi-Tenant User Isolation**: Bcrypt password hashing (`rounds=12`) and stateless JWT authorization ensuring users only ever access their own documents, chat sessions, and citations.
- **Robust PDF Ingestion**: PyMuPDF extraction with whitespace normalization, control character stripping, hyphenation reconstruction, and password-protected PDF rejection.
- **Dense Vector Search**: `sentence-transformers/all-MiniLM-L6-v2` generating 384-dimensional dense vectors stored in a persistent ChromaDB collection with cosine distance indexing.
- **Stage-2 Neural Reranking**: `cross-encoder/ms-marco-MiniLM-L-6-v2` joint cross-attention scoring over candidate chunks, achieving **100% Hit Rate@5** and **99.38% Recall@5** on academic benchmarks.
- **Source Provenance & Evidence Verification**: Clickable inline citation markers `[1]` opening a verified page-serving viewer (`GET /api/documents/{id}/pages/{page}`).
- **Zero-Hallucination Safe Fallback**: Automated abstention when evidence is insufficient or queries fall outside the ingested document corpus.
- **Empirical Research Dashboard**: Interactive Recharts visualizations with longitudinal experiment diffs, latency breakdowns, and CSV/JSON query metric exports.
- **Production Hardening**: Distributed `X-Request-ID` tracking, sliding-window rate limiting (60 req/min), path traversal defense, and security response headers.

---

## 5. Technology Stack
| Layer | Technologies | Role in System |
|---|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS, Recharts, Lucide Icons | Responsive SPA, interactive evidence inspection, real-time charts |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2, Python 3.10+ | Asynchronous REST API, schema validation, middleware |
| **Database** | SQLite (`aiosqlite`) / PostgreSQL | Relational metadata persistence (users, documents, chat sessions) |
| **Vector DB** | ChromaDB (Persistent Client) | High-performance dense vector storage & cosine similarity search |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` | 384-dimensional dense semantic vector generation |
| **Reranker** | HuggingFace `ms-marco-MiniLM-L-6-v2` | Cross-encoder contextual reranker |
| **LLM Reasoning**| Google Gemini (`gemini-3.1-flash-lite`) | Grounded answer synthesis and document comparison |
| **PDF Extraction**| PyMuPDF (`fitz`) | C-based high-throughput page-by-page text parsing |
| **Security** | Bcrypt, Python-JOSE, Rate Limiting | Password hashing, JWT auth, request throttling |

---

## 6. Installation & Environment Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))
- Git

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/RAGMate.git
cd RAGMate
```

### Step 2: Backend Setup
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```
Edit `backend/.env` and configure:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
JWT_SECRET_KEY=generate_a_random_32_character_secret_key
DATABASE_URL=sqlite+aiosqlite:///./ragmate.db
```

### Step 3: Frontend Setup
```bash
cd ../frontend
npm install
npm run build # verifies production build
```

---

## 7. Running the Application

### Running Backend API
```bash
cd backend
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Swagger Docs: `http://localhost:8000/docs`
- Interactive ReDoc: `http://localhost:8000/redoc`

### Running Frontend
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 8. Docker Deployment
DocuRAG includes production-ready Docker configurations for containerized execution.

```bash
# Build and run backend + frontend + persistent volumes
docker-compose up --build -d
```
Services spun up:
- `backend`: Exposed on port `8000` with mounted volumes for ChromaDB and uploads.
- `frontend`: Multi-stage Alpine Nginx serving optimized static assets on port `5173`.

---

## 9. Testing & Quality Assurance
DocuRAG includes a test suite covering unit logic, integration flows, multi-tenant isolation, IDOR security, and performance profiling.

### Run Full Test Suite
```bash
cd backend
.\venv\Scripts\pytest tests -v
```
**Current Status:** `113 / 113 passed` (56.89s execution duration).

### Run Security & Hardening Tests Only
```bash
.\venv\Scripts\pytest tests/test_security_and_hardening.py -v
```

### Run Performance & Resilience Tests Only
```bash
.\venv\Scripts\pytest tests/test_performance_and_resilience.py -v
```

---

## 10. Quantitative Research Evaluation
DocuRAG incorporates an evaluation dataset of **60 manually verified questions** across a **24-page academic corpus** (3 peer-reviewed research papers).

To execute the benchmark engine:
```bash
python -m evaluation.scripts.run_evaluation
```
Results and analysis are output to `evaluation/results/` and visualized within the frontend **Evaluation Dashboard** (`/evaluation`).

---

## 11. Security Considerations
- **Untrusted Document Context:** The prompt engine instructs the LLM that retrieved document excerpts are untrusted evidence and strictly forbids instruction execution from context text.
- **Path Traversal Defense:** Uploaded filenames are sanitized with regex character replacement and target directory boundaries are asserted using `Path.resolve()`.
- **Encrypted PDF Handling:** Password-protected or encrypted PDFs are proactively rejected with clean HTTP 400 responses.
- **Request Throttling:** Resource-intensive routes are throttled to 60 req/min per IP with HTTP 429 and `Retry-After`.
- **Security Headers:** Every response emits `X-Request-ID`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: strict-origin-when-cross-origin`.

---

## 12. License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
