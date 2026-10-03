# RAGMate: AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation (RAG)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Project Title
**AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation (RAG)**
*Academic Degree / Level: Master of Computer Applications (MCA)*

---

## 2. Overview
**RAGMate** is an enterprise-grade, academically rigorous Document Intelligence and Question Answering system based on Retrieval-Augmented Generation (RAG). It enables users to upload PDF research papers, technical manuals, and multi-page reports, automatically parses and chunks text with preserved page numbers, generates dense semantic embeddings, stores vectors in a persistent vector database (ChromaDB), retrieves contextually relevant snippets, optionally applies cross-encoder reranking, and synthesizes hallucination-controlled, fully cited answers using Google Gemini.

Furthermore, RAGMate integrates an **Academic Evaluation Suite** that empirically benchmarks three distinct retrieval paradigms:
1. **Baseline**: Traditional Keyword BM25 Retrieval
2. **Proposed**: Dense Semantic Vector Retrieval (ChromaDB + Sentence Transformers)
3. **Enhanced**: Dense Retrieval + Cross-Encoder Reranking

All evaluations are quantified using formal Information Retrieval (IR) and NLP metrics: Precision@K, Recall@K, Hit Rate@K, Mean Reciprocal Rank (MRR), Faithfulness, and Latency.

---

## 3. Problem Statement
Traditional Large Language Models (LLMs) suffer from three critical shortcomings in academic and professional contexts:
1. **Hallucination**: Generating plausible-sounding yet factually inaccurate statements.
2. **Knowledge Stagnation**: Inability to answer questions regarding proprietary, private, or recently published documents without costly fine-tuning.
3. **Lack of Provenance**: Inability to provide verifiable page-level citations for generated answers.

Directly feeding entire books or multi-page PDF documents into LLM context windows incurs prohibitive token costs, latency spikes, and the "lost-in-the-middle" attention phenomenon. RAGMate solves these challenges through modular text chunking, persistent vector search, strict grounding prompts, and provenance-tracked page citations.

---

## 4. Objectives
- Provide secure user authentication (JWT + Bcrypt) and tenant isolation for documents.
- Process arbitrary multi-page PDFs using high-performance C-based text extraction (`PyMuPDF`).
- Maintain exact page-number metadata for every chunk generated.
- Generate high-dimensional vector embeddings locally using `sentence-transformers/all-MiniLM-L6-v2`.
- Store and query embeddings with millisecond latency in ChromaDB.
- Formulate strict grounding prompts for Google Gemini to eliminate ungrounded hallucinations.
- Display clickable page citations and excerpt previews for every answer.
- Support multi-turn chat sessions with context sliding and document scoping (single-doc, multi-doc, all-doc).
- Conduct empirical research experiments comparing BM25, Dense Retrieval, and Cross-Encoder Reranking.

---

## 5. Key Features
- **User Authentication & Authorization**: Secure signup, login, JWT token management, and per-user document isolation.
- **Robust PDF Parsing**: Page-by-page extraction, whitespace normalization, header/footer filtering, and empty/scanned document detection.
- **Configurable Chunking Engine**: Parameterized chunk size (800–1200 characters/tokens) with sliding overlap (100–200) preserving page numbers.
- **Local Embedding Generation**: Cached HuggingFace SentenceTransformer models running on CPU/GPU without external API latency.
- **Vector DB Lifecycle**: Dynamic insertion, collection management, metadata filtering by `user_id` and `document_id`, and cascade deletion.
- **Hallucination Safeguards**: Explicit unanswerable detection when similarity falls below confidence thresholds.
- **Source Provenance**: Granular citations highlighting Document Name, Page Number, and Exact Text Snippet.
- **Interactive Academic UI**: Clean, professional Tailwind CSS dashboard with responsive sidebar navigation, upload progress, real-time chat, and evaluation charts.
- **Empirical Research Benchmarking**: Automated test suite executing verified queries across 3 retrieval regimes with real-time metric visualization.

---

## 6. High-Level Architecture
```
                           +----------------------+
                           |    React Frontend    |
                           |  (Vite + Tailwind)   |
                           +----------+-----------+
                                      | HTTP / REST
                                      v
                           +----------------------+
                           |   FastAPI Backend    |
                           +----------+-----------+
                                      |
         +----------------------------+----------------------------+
         |                            |                            |
         v                            v                            v
+------------------+         +------------------+         +------------------+
| Relational DB    |         | PDF Pipeline     |         | RAG & LLM Engine |
| (SQLite/Postgres)|         | (PyMuPDF)        |         | (ChromaDB+Gemini)|
| - Users          |         | - Page Extract   |         | - Vector Search  |
| - Documents      |         | - Text Clean     |         | - Cross-Rerank   |
| - Chat Sessions  |         | - Chunking       |         | - Prompt Ground  |
| - Messages       |         | - Embeddings     |         | - Page Citations |
+------------------+         +------------------+         +------------------+
```

---

## 7. Technology Stack
| Layer | Technologies | Rationale |
|---|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS, React Router DOM, Axios, Lucide Icons | Fast, modern, responsive UI with zero bloated UI libraries. |
| **Backend API** | FastAPI, Pydantic v2, Uvicorn, Python 3.10+ | Asynchronous high-throughput REST API with automatic OpenAPI docs. |
| **PDF Extraction** | PyMuPDF (Fitz) | High speed, robust C-level parser retaining exact page structure. |
| **Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) | Compact (384-d), fast inference, excellent semantic retrieval accuracy. |
| **Vector Database** | ChromaDB (Persistent) | Lightweight, reliable local vector storage with cosine/L2 metadata filtering. |
| **Reranker** | Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) | State-of-the-art precision reranking for candidate chunks. |
| **LLM Reasoning** | Google Gemini (`gemini-1.5-flash` / `gemini-1.5-pro`) | High-speed, large context window, accurate instruction following. |
| **Relational DB** | SQLite (Async via `aiosqlite`) / PostgreSQL | Modular SQLAlchemy 2.0 async engine. |
| **Auth & Security** | JWT (HS256) + Bcrypt Password Hashing | Industry standard stateless session authentication. |

---

## 8. Project Structure
```text
RAGMate/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI Routers (auth, documents, chat, evaluation)
│   │   ├── database/         # SQLAlchemy engine, session, Base models
│   │   ├── models/           # ORM Entities (User, Document, ChatSession, Message)
│   │   ├── services/         # Core business logic (PDF, chunker, embeddings, Chroma, Gemini, eval)
│   │   ├── utils/            # JWT, password hashing, validation helpers
│   │   ├── config.py         # Pydantic BaseSettings
│   │   └── main.py           # FastAPI application entrypoint & middleware
│   ├── chroma_data/          # Persistent ChromaDB vector collections
│   ├── uploads/              # Local disk storage for uploaded PDFs
│   ├── tests/                # Automated pytest suite (PDF, chunking, retrieval, API)
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Backend environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI widgets (Navbar, Sidebar, Modals, Cards)
│   │   ├── pages/            # Login, Register, Dashboard, Documents, Chat, Evaluation
│   │   ├── services/         # Axios API clients
│   │   ├── context/          # Auth and Notification contexts
│   │   ├── App.jsx           # App layout and route declarations
│   │   └── main.jsx          # React DOM root
│   ├── package.json          # Node dependencies
│   ├── tailwind.config.js    # Tailwind configuration
│   └── vite.config.js        # Vite build tool settings
├── evaluation/
│   ├── evaluation_questions.csv # Academic benchmark question set with ground truth
│   └── results/              # Measured JSON/CSV benchmark outputs
├── docs/
│   ├── architecture.md       # Detailed technical design document
│   ├── api.md                # REST API specifications and payloads
│   └── methodology.md        # Academic research methodology and viva notes
├── sample_documents/         # Sample academic papers for initial testing
├── .gitignore
├── .env.example
└── README.md
```

---

## 9. Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Git
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

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
# Edit .env and supply your GEMINI_API_KEY and a secure JWT_SECRET_KEY
```

### Step 3: Frontend Setup
```bash
cd ../frontend
npm install
npm run build # verify build
```

---

## 10. Running the Application

### Start Backend API Server
```bash
cd backend
# With venv activated:
uvicorn app.main:app --reload --port 8000
```
*API Swagger Documentation will be accessible at: `http://localhost:8000/docs`*

### Start Frontend Dev Server
```bash
cd frontend
npm run dev
```
*Web Application will be accessible at: `http://localhost:5173`*

---

## 11. Academic Evaluation & Research Methodology
The evaluation module benchmarks queries across three retrieval configurations:
$$\text{Precision@K} = \frac{|\text{Relevant Chunks Retrieved in Top K}|}{K}$$
$$\text{Recall@K} = \frac{|\text{Relevant Chunks Retrieved in Top K}|}{|\text{Total Relevant Chunks for Query}|}$$
$$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$

Results are saved to `evaluation/results/` and visualized interactively in the frontend Evaluation Dashboard.

---

## 12. License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
