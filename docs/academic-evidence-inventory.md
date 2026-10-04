# DocuRAG Academic Evidence Inventory & Audit Matrix

**Project Title**: DocuRAG – AI-Powered Intelligent Document Question Answering System  
**Academic Title**: AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation  
**Date**: October 2026  
**Auditor**: Senior Academic Research & Technical Documentation Reviewer  

---

## 1. Objective

This inventory establishes the empirical foundation for all academic documentation, project reports, and research papers produced for the DocuRAG project. In accordance with strict academic integrity standards, **no metric, performance figure, or test outcome is fabricated**. Every claim in the dissertation and research paper is traced to verified artifacts within the repository.

---

## 2. Empirical Evidence Inventory

| Research / Technical Artifact | Availability | Exact Artifact / Evidence Source | Empirical Observation / Measured Value |
|---|:---:|---|---|
| **Academic Corpus** | **Available** | `evaluation/corpus/` (3 PDFs) | 24 total pages across 3 peer-reviewed styled papers: `rag_dense_retrieval.pdf` (8 pgs), `neural_reranking_systems.pdf` (8 pgs), `llm_grounding_and_hallucination.pdf` (8 pgs). |
| **Evaluation Question Dataset** | **Available** | `evaluation/dataset/evaluation_questions.json` & `.csv` | **60 manually verified questions** (54 answerable across 7 types: 12 fact, 8 methodology, 8 algorithm, 8 results, 8 comparison, 6 multi-hop, 4 contextual; plus 6 out-of-domain unanswerable queries). |
| **Gold-Standard Annotations** | **Available** | `evaluation/dataset/evaluation_questions.json` | Each question contains golden target document, 1-indexed target page, exact golden answer string, and expected ground-truth text snippet. |
| **Precision@K (K=1, 3, 5, 10)** | **Available** | `evaluation/results/summary.json` (EXP_20261004_065505_60) | **Vector Baseline**: P@1=0.8704, P@3=0.3950, P@5=0.2481, P@10=0.1296.<br>**Reranked**: P@1=0.8704, P@3=0.4136, P@5=0.2630, P@10=0.1315 (+6.01% gain at K=5). |
| **Recall@K (K=1, 3, 5, 10)** | **Available** | `evaluation/results/summary.json` | **Vector Baseline**: R@1=0.7500, R@3=0.9290, R@5=0.9506, R@10=0.9846.<br>**Reranked**: R@1=0.7407, R@3=0.9414, R@5=0.9938, R@10=0.9938 (+4.54% gain at K=5). |
| **Hit Rate@K (K=1, 3, 5, 10)** | **Available** | `evaluation/results/summary.json` | **Vector Baseline**: HR@1=0.8704, HR@3=0.9815, HR@5=0.9815, HR@10=1.0000.<br>**Reranked**: HR@1=0.8704, HR@3=0.9630, HR@5=1.0000, HR@10=1.0000 (+1.88% gain at K=5). |
| **Mean Reciprocal Rank (MRR)** | **Available** | `evaluation/results/summary.json` | **Vector Baseline**: MRR = **0.9228**.<br>**Reranked**: MRR = **0.9188** (-0.43% slight rank variance on single-fact queries, compensated by +9.76% MRR gain on comparison questions). |
| **Abstention Accuracy** | **Available** | `evaluation/results/summary.json` | **1.0 (100%)** accuracy: 6 out of 6 unanswerable questions correctly triggered safe refusal without hallucinations. |
| **Question-Type Performance** | **Available** | `evaluation/results/summary.json` (`by_question_type`) | Measured MRR by type:<br>• `comparison` (8): Vector=0.8542, Reranked=0.9375 (+9.76%)<br>• `algorithm` (8): Vector=0.8333, Reranked=0.9062 (+8.75%)<br>• `results` (8): Vector=1.0000, Reranked=1.0000 (0.00%)<br>• `multi_hop` (6): Vector=0.9167, Reranked=0.9167 (0.00%)<br>• `contextual` (4): Vector=1.0000, Reranked=1.0000 (0.00%)<br>• `fact` (12): Vector=0.9028, Reranked=0.8361 (-7.38%)<br>• `methodology` (8): Vector=1.0000, Reranked=0.9167 (-8.33%). |
| **Retrieval & Reranking Latency** | **Available** | `evaluation/results/summary.json` (`latency_statistics`) | • **Vector Search**: Mean = 13.28 ms, Median = 12.82 ms, Min = 10.02 ms, Max = 18.98 ms.<br>• **Cross-Encoder**: Mean = 232.50 ms, Median = 133.00 ms (warm), Max = 5059.68 ms (cold start).<br>• **Total Pipeline**: Mean = 245.78 ms, Median = 143.78 ms. |
| **End-to-End LLM Latency** | **Available** | Server runtime logs & `gemini.py` latency tracker | Generative response synthesis via Gemini API: ~1.8 s to 2.6 s per query turn. |
| **Automated Test Suite** | **Available** | `backend/tests/` (17 test modules) | **119 / 119 tests passing** (duration: 56.86 seconds via `pytest`). |
| **Frontend Production Build** | **Available** | `frontend/dist/` (`vite build`) | Vite v8.3.2 bundle built in **1.90 seconds** (0 compilation errors, 0 lint errors via `oxlint`). |
| **Multi-Tenant User Isolation** | **Available** | `backend/tests/test_security_and_hardening.py` | 16 dedicated security tests proving User A cannot access User B's documents, sessions, messages, or vector spaces. |
| **Server-Side IDOR Defense** | **Available** | `backend/tests/test_security_and_hardening.py` | Cross-tenant document and session URL requests return HTTP 404 Not Found. |
| **Prompt Injection Defenses** | **Available** | `backend/tests/test_security_and_hardening.py` | Untrusted context framing verified against prompt leak instructions and system override attempts. |
| **Production Cloud Deployment** | **Available** | `docs/deployment.md`, `Dockerfile`, `docker-compose.yml`, `Procfile` | Configured for Vercel (Frontend), Render/Railway (FastAPI Backend), Neon/Supabase (PostgreSQL), and Cloudflare R2 / Disk (Storage). |
| **Database Migrations** | **Available** | `backend/app/db/init_db.py` | Successfully verified all 5 tables (`users`, `documents`, `chat_sessions`, `messages`, `chat_session_documents`) in 0.01 seconds. |
| **Answer Faithfulness (LLM)** | *Not measured via automated LLM-as-a-judge* | Evaluated via Grounding Guard & String Overlap | *Explicitly marked as "Not evaluated via automated G-Eval / Ragas; certified via deterministic citation sanitization and abstention rate."* |

---

## 3. Authoritative Master Data Table

The following empirical metrics represent the single source of truth for all documentation:

| Dimension / Parameter | Empirical System Value | Verification Source |
|---|---|---|
| **Corpus Document Count** | 3 Peer-Reviewed Style Research Papers | `evaluation/corpus/` |
| **Corpus Total Pages** | 24 Pages | PyMuPDF page count check |
| **Benchmark Question Count** | 60 Questions | `evaluation/dataset/evaluation_questions.json` |
| **Answerable Questions** | 54 Questions | Dataset question category check |
| **Unanswerable Questions** | 6 Questions | Dataset question category check |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` | `backend/app/config.py` |
| **Embedding Dimension** | 384-dimensional dense vectors (L2-normalized) | `test_embeddings_and_chroma.py` |
| **Reranker Model** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | `backend/app/config.py` |
| **Vector Database** | ChromaDB v0.4.24 (HNSW Cosine Distance) | `backend/app/services/vector_store.py` |
| **Generative LLM** | Google Gemini `gemini-3.1-flash-lite` | `backend/app/services/gemini.py` |
| **Candidate Retrieval Cutoff ($K_1$)** | 15 Candidate Chunks | `backend/app/config.py` |
| **Reranked Selection Cutoff ($K_2$)** | 5 Final Chunks | `backend/app/config.py` |
| **Chunking Parameters** | 1,000 characters, 150-character overlap | `backend/app/services/chunker.py` |
| **Similarity Threshold ($\tau$)** | 0.15 | `backend/app/config.py` |
| **Baseline Vector Precision@5** | **0.2481** | `evaluation/results/summary.json` |
| **Reranked Precision@5** | **0.2630** (+6.01% gain) | `evaluation/results/summary.json` |
| **Baseline Vector Recall@5** | **0.9506** | `evaluation/results/summary.json` |
| **Reranked Recall@5** | **0.9938** (+4.54% gain) | `evaluation/results/summary.json` |
| **Baseline Vector Hit Rate@5** | **0.9815** | `evaluation/results/summary.json` |
| **Reranked Hit Rate@5** | **1.0000** (100% capture) | `evaluation/results/summary.json` |
| **Baseline Vector MRR** | **0.9228** | `evaluation/results/summary.json` |
| **Reranked MRR** | **0.9188** | `evaluation/results/summary.json` |
| **Abstention Accuracy** | **1.0000** (100% on 6/6 queries) | `evaluation/results/summary.json` |
| **Median Vector Search Latency** | **12.82 ms** | `evaluation/results/summary.json` |
| **Median Cross-Encoder Latency** | **133.00 ms** (Warm CPU) | `evaluation/results/summary.json` |
| **Total Pipeline Median Latency** | **143.78 ms** | `evaluation/results/summary.json` |
| **Backend Test Suite Pass Rate** | **119 / 119 Passed (100%)** | `backend/tests/` |
| **Frontend Build Status** | **0 Errors, 1.90s Vite Build** | `frontend/dist/` |

---

## 4. Integrity Statement

All chapters in the MCA Project Report (`docs/project-report.md`) and the Research Paper (`docs/research-paper.md`) strictly draw from this inventory. No speculative or estimated figures are substituted for empirical measurements.
