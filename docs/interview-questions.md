# DocuRAG — Technical Interview, HR Placement & Professional Profiles Guide
**Academic Title:** *AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation*  
**Audience:** Technical Recruiters, Software Engineering Hiring Managers, and Placement Interviewers  

---

## 1. Top 10 Technical & Behavioral Placement Interview Questions

### Q1. Tell me about your major project and what motivated you to build it.
- **Answer:**
  *"I developed **DocuRAG**, an enterprise document question-answering system designed to eliminate Large Language Model hallucinations on private PDF documents. Standard LLMs cannot access private corporate data and frequently fabricate answers with fake citations. I engineered a two-stage retrieval pipeline combining fast dense vector embeddings in ChromaDB with a neural cross-encoder re-ranker. Every answer includes verifiable inline citations that link directly to exact page numbers and highlighted excerpts. In our 60-question benchmark, the re-ranker boosted Precision@5 by +6.01%, achieved a 100% Hit Rate@5, and eliminated hallucinations on out-of-domain queries."*

### Q2. What was your specific individual role in the project?
- **Answer:**
  *"I architected and implemented the entire end-to-end system independently:
  1. Built the asynchronous FastAPI backend and PyMuPDF ingestion engine.
  2. Implemented the two-stage RAG pipeline (`all-MiniLM-L6-v2` + `ms-marco-MiniLM-L-6-v2`).
  3. Developed the adaptive multi-document fair balancing algorithm and algorithmic citation sanitizer.
  4. Designed the responsive React 18 single-page application with an interactive Evidence Drawer.
  5. Built the 60-question Cranfield benchmark suite and wrote 119 automated regression tests."*

### Q3. What was the hardest technical challenge you encountered and how did you resolve it?
- **Answer:**
  *"The hardest challenge was **Multi-Document Starvation** during cross-document comparisons. When comparing a 15-page paper with a 4-page paper, global cosine similarity in ChromaDB returned chunks almost exclusively from the 15-page paper because of its sheer volume and repetitive topical terms. As a result, the second paper had zero retrieved chunks, making cross-document synthesis impossible.
  I solved this by formulating an **Adaptive Document-Balancing Algorithm**: the pipeline partitions candidates into per-document buckets and guarantees a proportional quota ($\lfloor K / T \rfloor$) from each active document before filling remaining slots with the highest overall re-rank scores. This boosted our Comparison Query MRR by **+9.76%**."*

### Q4. Tell me about a difficult bug that took the most time to diagnose and fix.
- **Answer:**
  *"During Phase 14 production hardening, our cascade deletion tests began throwing `sqlite3.IntegrityError: FOREIGN KEY constraint failed`.
  In Phase 9, I had designed a 'soft tombstone' feature: when a document was deleted, its link in `chat_session_documents` was marked `is_active = 0` so historic chat sessions could notify the user that a document had been removed. However, when we enabled strict foreign key pragmas in SQLite (`PRAGMA foreign_keys = ON;`), deleting a parent row from `documents` violated the foreign key constraint on the tombstoned link row.
  I resolved it by decoupling the cascade lifecycle: in PostgreSQL production, table relationships use explicit foreign key cascades, while in SQLite development, tombstoned session links are cleaned up gracefully in application logic before executing document deletion."*

### Q5. What key technical lessons did you learn from this project?
- **Answer:**
  *"1. **RAG is fundamentally an Information Retrieval problem**: The best generative LLM cannot answer correctly if the retrieval engine feeds it noisy or irrelevant context. Two-stage coarse-to-fine retrieval is essential for high precision.
  2. **Never trust raw LLM output for citations**: Models easily fabricate page numbers or hallucinate non-existent citation indices; a deterministic post-processing sanitizer is mandatory in production.
  3. **Multi-tenancy must be enforced at every layer**: User isolation cannot be an afterthought; it must be enforced at the API gateway, the relational database foreign keys, and the vector database metadata filters."*

### Q6. What would you improve or do differently if you had another month?
- **Answer:**
  *"I would implement **ColBERT-style token-level late interaction** (MaxSim operator). While our cross-encoder performs exceptionally well, its inference time scales linearly ($O(M)$) on CPU. ColBERT pre-computes token embeddings, achieving cross-encoder accuracy at near bi-encoder speeds. I would also integrate **Tesseract OCR** directly into PyMuPDF to process scanned image-only PDFs."*

### Q7. Why did you choose RAG over fine-tuning an open-source model like Llama-3?
- **Answer:**
  *"Fine-tuning modifies parametric model weights. It is computationally expensive, requires hours or days of GPU training whenever a user uploads a new PDF, suffers from catastrophic forgetting, and does *not* provide guaranteed source citations. RAG is non-parametric: new documents are indexed in seconds, answers are grounded in exact retrieved text, and every claim is backed by clickable page-level citations."*

### Q8. Which parts did you build from scratch vs. using existing libraries?
- **Answer:**
  *"I used established open-source libraries for foundational tasks: PyMuPDF for C++ PDF parsing, SentenceTransformers for transformer inference, ChromaDB for HNSW indexing, and FastAPI for ASGI routing.
  I built the following from scratch:
  - The recursive token-bounded chunking and offset tracking logic.
  - The two-stage retrieval orchestration and score normalization pipelines.
  - The adaptive multi-document balancing algorithm.
  - The anti-jailbreak prompt envelope and deterministic citation sanitizer.
  - The contextual query rewriting service for multi-turn chat.
  - The complete React 18 UI, interactive Evidence Drawer, and PDF page viewer."*

### Q9. What happens if the external Google Gemini API goes down?
- **Answer:**
  *"DocuRAG is engineered with fault tolerance:
  1. The retrieval pipeline (ChromaDB + CrossEncoder) is completely local and operational without external APIs.
  2. If Gemini fails or times out, `gemini_service.py` intercepts the error and returns an HTTP 503 advisory.
  3. Because the LLM service is decoupled behind a clean abstraction, the backend can easily be reconfigured to failover to OpenAI GPT-4, Anthropic Claude, or a local self-hosted model running on Ollama/vLLM."*

### Q10. How would you scale this architecture to support 100,000 active concurrent users?
- **Answer:**
  *"1. **Stateless API Horizontal Scaling**: Deploy FastAPI across Kubernetes pods with horizontal pod autoscalers (HPA) behind an AWS Application Load Balancer.
  2. **Distributed Vector Cluster**: Migrate from embedded ChromaDB to a distributed Qdrant or Milvus cluster with IVF-PQ indexing and read replicas.
  3. **Asynchronous Ingestion Queues**: Offload heavy PDF parsing and vector generation to Celery workers using Redis/RabbitMQ.
  4. **Semantic Caching**: Deploy Redis with vector similarity caching to serve identical or semantically duplicate queries instantly without re-invoking the LLM."*

---

## 2. Professional Resume Project Description

```text
DocuRAG – AI-Powered Intelligent Document Question Answering System
Technologies: Python, FastAPI, React 18, PostgreSQL, ChromaDB, SentenceTransformers, CrossEncoder, Google Gemini, Docker, Pytest
• Engineered a multi-tenant enterprise RAG platform enabling grounded Q&A across multi-page PDFs with verified inline citations.
• Designed a two-stage coarse-to-fine retrieval pipeline pairing bi-encoder vector search (all-MiniLM-L6-v2) with cross-encoder neural re-ranking (ms-marco-MiniLM-L-6-v2), boosting Precision@5 by +6.01% and achieving a 100% Hit Rate@5.
• Formulated an adaptive multi-document balancing algorithm that eliminated document starvation, improving Comparison Query MRR by +9.76%.
• Built an algorithmic citation verification engine that prunes hallucinated citations and extracts exact snippets for an interactive React Evidence Drawer with on-demand rendered PDF page views.
• Achieved 100% pass rate across 119 automated test suites with zero security vulnerabilities (IDOR, SQLi, Prompt Injection).
• Deployed to production using a decoupled multi-cloud architecture (Vercel Edge CDN, Render ASGI compute, Neon Serverless PostgreSQL).
```

---

## 3. GitHub Project Descriptions

### Short Description (GitHub About Section, <160 characters):
```text
Enterprise two-stage RAG document QA platform with cross-encoder re-ranking, fair multi-document balancing, verified citations, and 100% Hit Rate@5.
```

### Detailed GitHub Repository README Highlights:
```markdown
# DocuRAG: Enterprise Two-Stage Document QA with Grounded Citations

**DocuRAG** is an enterprise-grade document question-answering platform built upon a coarse-to-fine Retrieval-Augmented Generation (RAG) architecture. It eliminates LLM hallucinations on private PDF documents by combining dense vector retrieval with neural cross-encoder re-ranking and deterministic citation verification.

### Key Highlights:
- **Two-Stage Coarse-to-Fine Retrieval**: Bi-encoder vector search (`all-MiniLM-L6-v2`, $M=15$) + Cross-Encoder re-ranking (`ms-marco-MiniLM-L-6-v2`, $K=5$).
- **100% Hit Rate@5**: Achieved a flawless 100% Hit Rate and 0.9938 Recall@5 across a 60-question Cranfield academic benchmark.
- **Deterministic Citation Sanitizer**: Every answer provides verified inline markers (`[1]`, `[2]`) linked to exact page numbers, snippets, and rendered PDF page views.
- **Adaptive Multi-Document Balancing**: Fair candidate sampling eliminates document starvation, boosting Comparison Query MRR by +9.76%.
- **Zero Hallucination on Unanswerable Queries**: Achieved 1.0000 Abstention Accuracy on adversarial out-of-domain queries.
- **Production Hardened**: 119/119 automated tests passing across 17 test modules; deployed across Vercel, Render, and Neon PostgreSQL.
```

---

## 4. Professional LinkedIn Project Post

```text
🚀 Excited to share my MCA Major Project: DocuRAG – Intelligent Document QA System using Retrieval-Augmented Generation (RAG)!

While Large Language Models (LLMs) are great at conversational synthesis, deploying them in enterprise environments is risky: they hallucinate, cannot access private documents, and lack auditable source citations.

To solve this, I designed and built DocuRAG, a full-stack, enterprise-grade document QA platform that makes AI answers verifiable, transparent, and grounded in private PDF documents.

💡 Key Architectural Highlights:
🔹 Two-Stage Coarse-to-Fine Retrieval: Combines fast 384-d bi-encoder vector search in ChromaDB (HNSW) with deep neural cross-encoder re-ranking (ms-marco-MiniLM-L-6-v2) modeling full query-passage joint token self-attention.
🔹 Adaptive Multi-Document Balancing: Solved "document starvation" during multi-paper comparisons, guaranteeing fair evidence quotas across all documents.
🔹 Deterministic Citation Verification: Built an algorithmic post-processor that verifies citation markers ([1], [2]), prunes hallucinated indices, and populates an interactive Evidence Drawer with on-demand rendered PDF page views.
🔹 Anti-Jailbreak Prompt Framing: Strict delimiter separation treating document content as untrusted data to defend against prompt injection.

📊 Measured Empirical Results (60-Question Cranfield Benchmark):
✅ 100.0% Hit Rate@5 (Flawless evidence capture)
✅ +6.01% Gain in Precision@5 (0.2481 ➔ 0.2630)
✅ +4.54% Gain in Recall@5 (0.9506 ➔ 0.9938)
✅ +9.76% Gain in Comparison Query MRR
✅ 1.0000 Abstention Accuracy (Zero hallucination on unanswerable questions)
✅ Sub-150ms median retrieval latency on CPU!

🛠️ Tech Stack:
FastAPI, React 18, Tailwind CSS, ChromaDB, PostgreSQL (SQLAlchemy), PyMuPDF, SentenceTransformers, Google Gemini 2.5 Flash, Docker, Pytest (119/119 tests passing).

A huge thank you to my project guide and faculty for their constant encouragement throughout this research!

#ArtificialIntelligence #MachineLearning #NLP #RAG #FastAPI #React #FullStack #Python #ChromaDB #Gemini #ComputerApplications #MCA
```
