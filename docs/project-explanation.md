# DocuRAG — Multi-Duration Project Explanations
**Academic Title:** *AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation*  
**Audience:** External Examiners, Department Evaluators, Professors, and Technical Interviewers  

---

## 1. 30-Second Project Introduction (Elevator Pitch)

> **"Tell me about your project."**

"Large Language Models frequently hallucinate and lack access to private organizational documents. To solve this, I developed **DocuRAG**, an intelligent document question-answering system using Retrieval-Augmented Generation. 

Built with **FastAPI, React, ChromaDB, and Google Gemini 2.5 Flash**, the system uses a **two-stage retrieval pipeline**: first over-fetching candidate chunks via 384-dimensional dense vector embeddings, and then re-ranking them using a deep **neural cross-encoder** to capture full query-document token self-attention. 

Every answer provides **deterministic inline citations** linking back to exact page numbers and highlighted excerpts. In empirical evaluation across a 60-question benchmark, our re-ranking pipeline achieved a **100% Hit Rate at Top-5** and **100% safe abstention** on out-of-domain queries, completely eliminating ungrounded hallucinations."

*(Spoken duration: ~35 seconds)*

---

## 2. 1-Minute Project Explanation (Comprehensive Overview)

> **"Give a concise 1-minute summary of what you built and how it works."**

"**DocuRAG** is an enterprise-grade document question-answering platform designed to make AI responses verifiable, transparent, and grounded in private PDF documents.

Standard generative AI cannot be audited—it makes unsupported claims and invents citations. Furthermore, naive vector search suffers from vocabulary mismatch and document starvation in multi-document queries. 

DocuRAG solves this through a clean, coarse-to-fine architecture:
1. When a user uploads a PDF, **PyMuPDF** extracts the text page-by-page, cleans typographic anomalies, and splits it into 500-token chunks with 100-token overlap.
2. Chunks are embedded into **ChromaDB** using `all-MiniLM-L6-v2`.
3. When a query is submitted, Stage 1 over-fetches 15 candidate chunks. An adaptive document balancer ensures fair sampling across all active documents.
4. Stage 2 passes these candidates to a **cross-encoder** (`ms-marco-MiniLM-L-6-v2`), which re-ranks them based on joint token attention, selecting the top 5 chunks.
5. **Google Gemini 2.5 Flash** synthesizes the answer under strict grounding instructions. An algorithmic sanitizer validates every inline marker `[1]`, `[2]` against actual chunks and extracts evidence snippets for our React Evidence Drawer.

In our 60-question Cranfield evaluation, re-ranking improved **Precision@5 by +6.01%**, **Recall@5 by +4.54%**, and achieved a **100.0% Hit Rate@5** with a median retrieval latency under 150 milliseconds."

*(Spoken duration: ~65 seconds)*

---

## 3. 3-Minute Academic Project Explanation (Professor & Evaluator Pitch)

> **"Walk us through your project, the architecture, your methodology, and your results."**

"Good morning, respected examiners. My MCA project is titled **AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation**, or **DocuRAG**.

### 1. Problem & Existing Limitations
While foundational Large Language Models show remarkable reasoning, they are black boxes bounded by static training data. When queried on proprietary or specialized documents, they suffer from probabilistic hallucination, lack verifiable citations, and cannot be trusted in legal, scientific, or corporate decision-making. Existing RAG implementations attempt to fix this, but they rely on naive single-stage vector retrieval, which creates a vector compression bottleneck, vocabulary mismatch, and document starvation during multi-document comparisons.

### 2. Proposed Architecture & Ingestion
To address these gaps, I engineered DocuRAG as a full-stack, multi-tenant system:
- The **Ingestion Engine** uses **PyMuPDF** to extract text while strictly tracking 1-indexed page boundaries. It detects encrypted PDFs and image-only scans to avoid pipeline crashes.
- The **Chunker** splits text into 500-token chunks with a 100-token sliding overlap using recursive separators.
- Chunks are vectorized using the `all-MiniLM-L6-v2` bi-encoder into $L_2$-normalized 384-dimensional embeddings and indexed in **ChromaDB** using an HNSW cosine index, tagged with `user_id` metadata for multi-tenant isolation.

### 3. Two-Stage Retrieval & Document Balancing
When a user asks a question, naive search often fails on subtle logic. DocuRAG introduces a **two-stage coarse-to-fine pipeline**:
- **Stage 1**: Fast bi-encoder vector search over-fetches a candidate pool of $M = 15$ chunks in ~13 milliseconds.
- For comparative queries spanning multiple PDFs, an **adaptive balancing algorithm** guarantees that candidates are sampled proportionally, preventing one long document from starving another.
- **Stage 2**: A deep **cross-encoder** (`ms-marco-MiniLM-L-6-v2`) evaluates full query-passage joint token self-attention across the 15 candidates, filtering out false positives and promoting the top $K = 5$ chunks in ~133 milliseconds.

### 4. Grounded Synthesis & Citation Verification
The top 5 chunks are assembled into an XML-delimited prompt envelope and passed to **Google Gemini 2.5 Flash**. The prompt instructs the model to answer strictly from the context, include inline citation markers `[1]`, `[2]`, and emit a standardized refusal string if the evidence is insufficient. An algorithmic citation sanitizer then validates the output, re-indexes markers sequentially, strips out-of-bounds citations, and populates an interactive Evidence Drawer displaying exact snippets and rendered PDF page views.

### 5. Empirical Evaluation & Results
We evaluated DocuRAG against a 60-question Cranfield benchmark across a 24-page academic corpus. The empirical results prove:
- **Precision@5 increased by +6.01%** (from 0.2481 to 0.2630).
- **Recall@5 increased by +4.54%** (from 0.9506 to 0.9938).
- **Hit Rate@5 reached 100.0%** (up from 98.15% in vector search).
- For complex Comparison and Algorithm queries, **MRR improved by +9.76% and +8.75%** respectively.
- The system achieved **1.0000 Abstention Accuracy** on out-of-domain queries, proving complete hallucination defense.

The platform is fully implemented with FastAPI, React 18, and PostgreSQL, passes all 119 automated test suites, and is deployed to production."

*(Spoken duration: ~3 minutes)*

---

## 4. 5-Minute End-to-End Technical Pipeline Explanation (Deep Architectural Walkthrough)

> **"Take us through the entire technical execution pipeline from the moment a user clicks in the UI to the final database record."**

"Let us trace the complete execution flow through DocuRAG across all 16 distinct operational stages:

```text
User Action
  ↓ (1)
React 18 SPA
  ↓ (2)
FastAPI Gateway & Auth Middleware
  ↓ (3)
Storage Provider & PyMuPDF Ingestion
  ↓ (4)
Text Sanitizer & Recursive Token Chunker
  ↓ (5)
SentenceTransformer Embedding Service (Singleton)
  ↓ (6)
ChromaDB HNSW Vector Indexing
  ↓ (7)
Chat Session & Contextual Query Rewriter
  ↓ (8)
Stage 1: Bi-Encoder Vector Candidate Retrieval (M = 15)
  ↓ (9)
Adaptive Multi-Document Fair Balancer
  ↓ (10)
Stage 2: Cross-Encoder Joint Token Attention Re-ranking (K = 5)
  ↓ (11)
Delimited Context Assembly & Anti-Injection Guard
  ↓ (12)
Google Gemini 2.5 Flash Grounded Synthesis
  ↓ (13)
Algorithmic Citation Sanitization & Snippet Extraction
  ↓ (14)
SQLAlchemy Transactional Persistence (PostgreSQL/SQLite)
  ↓ (15)
FastAPI Response Serialization
  ↓ (16)
React UI Rendering: Markdown Answer, Interactive Citations & Evidence Drawer
```

### Stage 1: Client Interaction (React 18 SPA)
The user accesses the responsive React 18 application built with Vite and Tailwind CSS. The user logs in via JWT authentication, uploads a multi-page PDF, or types a question into an active chat session.

### Stage 2: Application Gateway & Security Middleware (FastAPI)
The request hits FastAPI via Uvicorn. The security middleware intercepts the request:
- Validates the OAuth2 `Authorization: Bearer <JWT>` header using `python-jose` with `HS256`.
- Extracts and verifies the authenticated `user_id`.
- Attaches a unique distributed tracing ID (`X-Request-ID`).
- Checks the in-memory sliding-window rate limiter (60 requests/minute per IP).
- Enforces production HTTP security headers (`nosniff`, `DENY`).

### Stage 3: Document Storage & PyMuPDF Extraction
If uploading a document:
- The `StorageProvider` strategy saves the raw file to local disk or AWS S3.
- `pdf_processor.py` validates the magic bytes, confirms it is not encrypted (`doc.is_encrypted`), and reads text page-by-page using PyMuPDF (`fitz`), tracking 1-indexed page numbers.
- If total extracted text is under 10 characters, it rejects the file with `ScannedPDFError`.

### Stage 4: Text Normalization & Recursive Chunking
`chunker.py` sanitizes ligature artifacts and reconnects hyphenated line wraps. It executes recursive character splitting with separators `["\n\n", "\n", " ", ""]` targeting 500 tokens with a 100-token sliding overlap. Each chunk object encapsulates its parent document ID, page number, chunk index, and character offsets.

### Stage 5: Dense Bi-Encoder Embeddings
`embedding_service.py` runs `sentence-transformers/all-MiniLM-L6-v2` loaded as a thread-safe singleton. It converts chunks into 384-dimensional dense vectors and performs explicit $L_2$-normalization ($\|\mathbf{v}\|_2 = 1.0$), mapping all chunks onto the unit hypersphere.

### Stage 6: ChromaDB Vector Indexing
The vectors, chunk text, and metadata (`user_id`, `document_id`, `page_number`) are inserted into ChromaDB's HNSW graph index configured with cosine distance.

### Stage 7: Query Submission & Contextual Query Rewriting
When the user submits a question in a chat session:
- If previous conversation turns exist, `query_rewriter.py` passes the chat history and current message to an LLM prompt to resolve pronouns and conversational references into a standalone search query.
- Example: *"What were its main results?"* $\rightarrow$ *"What were the main results of the Transformer architecture in Attention Is All You Need?"*

### Stage 8: Stage 1 Vector Candidate Retrieval
The standalone query is embedded into a 384-d vector. ChromaDB executes an HNSW approximate nearest neighbor search with metadata filtering (`user_id = current_user.id`). It over-fetches candidate pool $M = 15$ chunks.

### Stage 9: Adaptive Document Balancing
If the query mode is multi-document or comparison intent is detected, candidates are partitioned into document buckets. Each document is allocated a proportional quota ($\lfloor K / T \rfloor$), preventing any single document from starving the others.

### Stage 10: Stage 2 Cross-Encoder Neural Re-Ranking
The 15 candidate chunks are evaluated using `cross-encoder/ms-marco-MiniLM-L-6-v2`. Unlike bi-encoders, the cross-encoder concatenates the query and passage into a single sequence: `[CLS] q [SEP] c_i [SEP]`. All transformer layers compute joint cross-attention between all query tokens and chunk tokens. The classification logit is converted via sigmoid into a normalized probability $\sigma_i \in [0, 1]$. Candidates are sorted, pruned below $\sigma_i < 0.15$, and the top $K = 5$ chunks are retained.

### Stage 11: Prompt Assembly & Anti-Injection Guard
`gemini_service.py` builds an XML-delimited prompt:
`=== BEGIN DOCUMENT CONTEXT === [Source 1: Doc (Page X)] ... === END DOCUMENT CONTEXT ===`
The prompt contains explicit instructions treating context as untrusted data, preventing document-embedded text from hijacking system behavior.

### Stage 12: Google Gemini 2.5 Flash Generation
The assembled prompt is transmitted via HTTPS to Google Gemini 2.5 Flash (temperature 0.2). Gemini generates a grounded response containing inline citation markers `[1]`, `[2]`. If unanswerable, it emits the mandatory refusal phrase.

### Stage 13: Algorithmic Citation Sanitization
`citation_sanitizer.py` parses the output via regex:
- Strips any citation index greater than 5 or less than 1.
- Normalizes non-sequential citations (e.g., `[3]` $\rightarrow$ `[1]`).
- Extracts 150-character contextual snippets highlighting the key evidence sentences.
- Assembles citation payloads linking document ID, page number, vector score, and re-rank score.

### Stage 14: Transactional Persistence
SQLAlchemy persists the user question, assistant response, and message citations into the relational database (`chat_messages` and `message_citations` tables) within a single ACID transaction.

### Stage 15 & 16: API Serialization & UI Evidence Drawer
FastAPI serializes the JSON payload. The React client renders the markdown response, formats clickable citation badges, and populates the slide-out Evidence Drawer. Clicking any citation opens the exact PDF page preview rendered on demand by the backend.

The entire pipeline executes in ~1.46 seconds end-to-end, providing 100% auditable evidence."

*(Spoken duration: ~5 minutes)*
