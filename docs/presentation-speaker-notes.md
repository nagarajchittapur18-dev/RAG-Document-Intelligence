# DocuRAG — Presentation Speaker Notes for MCA Viva Voce
**Academic Title:** *AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation*  
**Format:** Detailed Speaker Guide for All 20 Presentation Slides  

---

### Slide 1: Title & Candidacy
- **Slide Objective:** Establish academic identity, project title, guide credentials, and professional composure.
- **What to Show:** Project title, candidate name, USN, guide name, department, institution logo.
- **What to Say:**  
  *"Good morning, respected external examiners, head of the department, and faculty members. My name is [STUDENT NAME], USN [USN]. Today, I am proud to present my MCA major project titled 'DocuRAG: AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation', carried out under the esteemed guidance of [GUIDE NAME]."*
- **Important Technical Point:** RAG stands for Retrieval-Augmented Generation, combining information retrieval with generative LLMs.
- **Possible Question:** *"What makes this project different from existing PDF chat wrappers?"*  
  *Answer:* *"Unlike naive wrappers that perform basic cosine similarity over embeddings, DocuRAG implements a two-stage coarse-to-fine pipeline pairing bi-encoders with cross-encoders, multi-document balancing, deterministic citation sanitization, and enterprise multi-tenant security."*

---

### Slide 2: Introduction to Document QA & LLMs
- **Slide Objective:** Contextualize the shift toward LLMs and explain why enterprise document processing requires specialized architectures.
- **What to Show:** Bullet points highlighting LLM capabilities, private data isolation, and why fine-tuning is impractical.
- **What to Say:**  
  *"In recent years, Large Language Models like GPT-4 and Gemini have revolutionized natural language understanding. However, in enterprise and academic domains, knowledge resides in private, proprietary PDFs—such as legal contracts, scientific papers, and compliance manuals. Fine-tuning models on these private documents is slow, cost-prohibitive, and causes catastrophic forgetting. RAG bridges this divide by retrieving exact document passages dynamically at query time and injecting them into the prompt."*
- **Important Technical Point:** Fine-tuning updates model weights ($\theta \leftarrow \theta - \eta \nabla L$); RAG updates context non-parametrically without retraining weights.
- **Possible Question:** *"Why not just fine-tune an open-source model like Llama on your documents?"*  
  *Answer:* *"Fine-tuning does not guarantee factual provenance or citation verification. When updated with new documents, fine-tuned models still hallucinate and require continuous, expensive GPU re-training."*

---

### Slide 3: Problem Statement
- **Slide Objective:** Formulate the core challenges that make standard LLMs unreliable.
- **What to Show:** Diagrams or callouts illustrating parametric cutoff, hallucination, lack of citations, and search failure.
- **What to Say:**  
  *"Our problem statement addresses three critical vulnerabilities: first, foundational models have a hard training cutoff and zero visibility into uploaded organizational files; second, when an LLM is uncertain, its maximum-likelihood token prediction objective compels it to generate plausible-sounding falsehoods—known as hallucinations; third, traditional lexical search tools suffer from term mismatch, while standard vector databases lack verification mechanisms to guarantee citation integrity."*
- **Important Technical Point:** LLMs are probabilistic sequence predictors, not knowledge lookup engines; hallucination is intrinsic to unconstrained autoregression.
- **Possible Question:** *"What is the difference between intrinsic and extrinsic hallucination?"*  
  *Answer:* *"Intrinsic hallucination directly contradicts the facts provided in the source text; extrinsic hallucination introduces outside claims that can neither be verified nor refuted by the source text."*

---

### Slide 4: Motivation & Industry Context
- **Slide Objective:** Justify the necessity of an auditable, enterprise-ready system.
- **What to Show:** Key industry drivers: verifiable AI, multi-tenancy, and computational tractability.
- **What to Say:**  
  *"In critical environments such as healthcare, legal discovery, and engineering, an unverified answer can lead to catastrophic legal or physical consequences. Decisions cannot be made on black-box assertions. Every factual claim must link to an exact page number and text snippet. Furthermore, organizations require strict multi-tenancy where departments share infrastructure without risking cross-tenant data leakage."*
- **Important Technical Point:** Auditability requires deterministic end-to-end traceability from the generated token back to character offsets in the raw PDF.
- **Possible Question:** *"What is multi-tenancy in your architecture?"*  
  *Answer:* *"Multi-tenancy guarantees that each user's uploaded documents, chunks, vectors in ChromaDB, and chat histories are strictly partitioned by their authenticated `user_id`, preventing any unauthorized access across tenants."*

---

### Slide 5: Existing Systems Analysis
- **Slide Objective:** Critique existing search and single-stage RAG baselines.
- **What to Show:** Comparative matrix contrasting BM25, direct LLMs, and naive single-stage RAG.
- **What to Say:**  
  *"When analyzing existing solutions, we observe three paradigms: traditional lexical search like BM25 is fast but fails when queries use synonyms or paraphrasing. Sending entire documents directly to LLMs is cost-prohibitive and suffers from attention degradation. Finally, naive single-stage RAG systems rely purely on bi-encoder cosine similarity, which suffers from vector compression bottlenecks and document starvation during multi-document queries."*
- **Important Technical Point:** Lexical search suffers from high false-negative rates due to synonymy and polysemy.
- **Possible Question:** *"What is the term mismatch problem in BM25?"*  
  *Answer:* *"If a query asks for 'heart attack' and the document says 'myocardial infarction', BM25 assigns zero relevance because there is no lexical token overlap."*

---

### Slide 6: Research Gap
- **Slide Objective:** Identify the scientific and engineering gaps our research resolves.
- **What to Show:** Four highlighted research gaps: vector compression, lost-in-the-middle, document starvation, and citation fabrication.
- **What to Say:**  
  *"Our literature review identified four critical research gaps: first, the vector compression bottleneck—compressing 500 tokens into a single 384-dimensional vector causes loss of fine-grained logical nuances; second, the 'Lost-in-the-Middle' phenomenon documented by Liu et al., where LLM recall drops when evidence is placed in the middle of long prompts; third, the absence of fair multi-document sampling; and fourth, the lack of algorithmic verification to catch fabricated citations."*
- **Important Technical Point:** Liu et al. (2024) demonstrated a U-shaped performance curve where LLMs attend primarily to the start and end of prompt context.
- **Possible Question:** *"How does two-stage retrieval solve the lost-in-the-middle problem?"*  
  *Answer:* *"The cross-encoder re-ranks candidates with high precision, pushing the single most relevant chunk to rank 1 at the absolute top of the prompt envelope where the LLM's attention is strongest."*

---

### Slide 7: Project Objectives
- **Slide Objective:** Enumerate the formal goals established and achieved in this project.
- **What to Show:** The 6 core research and software engineering objectives.
- **What to Say:**  
  *"To resolve these gaps, we defined six concrete objectives: build an asynchronous multi-tenant PDF ingestion engine; construct a two-stage retrieval pipeline combining bi-encoder search with cross-encoder re-ranking; formulate an adaptive multi-document balancing algorithm; engineer a deterministic citation verification engine; evaluate the system against a 60-question Cranfield benchmark; and validate with 100% test coverage for cloud deployment."*
- **Important Technical Point:** Every objective is accompanied by verifiable empirical code and test assertions in the repository.
- **Possible Question:** *"Did you achieve all six objectives?"*  
  *Answer:* *"Yes, all six objectives were fully realized, verified by 119 automated test suites and measured empirically under experiment `EXP_20261004_065505_60`."*

---

### Slide 8: Proposed System: DocuRAG
- **Slide Objective:** Introduce the DocuRAG platform and its architectural subsystems.
- **What to Show:** Overview diagram showing Client Tier, API Gateway, Two-Stage Engine, and Grounded Generation.
- **What to Say:**  
  *"We propose DocuRAG—an end-to-end intelligent document question-answering platform. DocuRAG integrates a responsive React 18 single-page application with an asynchronous FastAPI gateway. The core processing engine pairs fast bi-encoder candidate retrieval in ChromaDB with deep neural cross-encoder re-ranking, fair multi-document sampling, and Google Gemini 2.5 Flash synthesis with algorithmic citation sanitization."*
- **Important Technical Point:** The architecture separates the fast retrieval tier ($O(\log N)$) from the computationally intensive re-ranking tier ($O(M)$).
- **Possible Question:** *"Why use Google Gemini 2.5 Flash instead of GPT-4?"*  
  *Answer:* *"Gemini 2.5 Flash provides exceptional reasoning latency (~1.3s), a large context window, excellent instruction adherence for structured citations, and cost-efficient API economics suited for production."*

---

### Slide 9: High-Level System Architecture
- **Slide Objective:** Present the complete four-tier architectural schematic.
- **What to Show:** Clean architectural block diagram displaying Client, Gateway, Services, and Persistence layers.
- **What to Say:**  
  *"This diagram illustrates DocuRAG's four-tier architecture. The React client communicates with the FastAPI gateway over HTTPS using signed JWT tokens. Ingestion flows from PyMuPDF through text sanitization and recursive chunking into SentenceTransformers and ChromaDB. Queries flow through contextual rewriting into ChromaDB HNSW search, pass through cross-encoder re-ranking, and feed into Gemini 2.5 Flash. Relational state is persisted across PostgreSQL or SQLite via SQLAlchemy."*
- **Important Technical Point:** The architecture uses Dependency Injection in FastAPI, making storage, database, and embedding services fully mockable and modular.
- **Possible Question:** *"How is multi-dialect database persistence achieved?"*  
  *Answer:* *"SQLAlchemy ORM abstracts the SQL dialect. The system automatically detects whether `DATABASE_URL` specifies SQLite or PostgreSQL, configuring WAL mode for SQLite or connection pooling with SSL for PostgreSQL."*

---

### Slide 10: The Complete RAG Execution Pipeline
- **Slide Objective:** Detail the step-by-step lifecycle of document ingestion and user querying.
- **What to Show:** Linear flowchart tracing Ingest $\rightarrow$ Embed $\rightarrow$ Query $\rightarrow$ Stage 1 $\rightarrow$ Balance $\rightarrow$ Stage 2 $\rightarrow$ Synthesize $\rightarrow$ Sanitize.
- **What to Say:**  
  *"Let us trace the complete execution pipeline. When a document is ingested, it is parsed page-by-page, cleaned, and split into 500-token chunks with 100-token overlap. Each chunk is embedded into an $L_2$-normalized 384-dimensional vector in ChromaDB. When a user asks a question, conversation history is used to rewrite follow-up queries. Stage 1 retrieves 15 candidates; multi-document balancing ensures equal document quotas; Stage 2 re-ranks using joint cross-attention to select the top 5 chunks; Gemini synthesizes the answer; and the citation sanitizer validates markers and loads the Evidence Drawer."*
- **Important Technical Point:** $L_2$ normalization maps vectors to the unit hypersphere ($\|\mathbf{v}\|_2 = 1.0$), making cosine similarity identical to the inner dot product ($\mathbf{q} \cdot \mathbf{v}$).
- **Possible Question:** *"Why do you over-fetch 15 candidates instead of 5 in Stage 1?"*  
  *Answer:* *"Bi-encoder search has high recall but moderate precision. Over-fetching $M = 15$ chunks ensures the true answering chunk is captured in the pool before the cross-encoder filters out false positives."*

---

### Slide 11: Technology Stack
- **Slide Objective:** Justify the selection of frameworks, libraries, and runtime components.
- **What to Show:** Categorized table covering Frontend, Backend, AI/NLP, Databases, Security, and Deployment.
- **What to Say:**  
  *"Our technology stack is carefully selected for performance and reliability: React 18 with Vite provides a sub-2-second build time and clean component rendering; FastAPI provides asynchronous ASGI routing; PyMuPDF offers high-speed C++ PDF extraction; SentenceTransformers and CrossEncoder handle neural embeddings and re-ranking; ChromaDB provides local HNSW indexing; PostgreSQL handles relational transactions; and Pytest guarantees quality with 119 automated tests."*
- **Important Technical Point:** FastAPI uses Pydantic v2 for sub-millisecond serialization and strict schema validation.
- **Possible Question:** *"Why did you choose PyMuPDF over PDFMiner or PyPDF2?"*  
  *Answer:* *"PyMuPDF is backed by the MuPDF C++ rendering library, parsing multi-page documents up to 10 times faster than pure Python parsers like PDFMiner, while preserving exact page numbers and layout structures."*

---

### Slide 12: Ingestion & Preprocessing Subsystem
- **Slide Objective:** Explain how unstructured PDFs are converted into clean, semantically rich chunks.
- **What to Show:** Text cleaning rules, encrypted PDF detection, scanned PDF detection, and chunking parameters.
- **What to Say:**  
  *"The ingestion engine must handle real-world document anomalies robustly. Our processor checks file magic bytes and detects encrypted PDFs proactively to prevent server crashes. If a PDF has no extractable text layer—such as a raw image scan—it raises a `ScannedPDFError`. Text is sanitized to reconnect hyphenated line breaks like 'multi-\nhead'. Then, recursive character splitting partitions text into 500-token chunks with 100-token overlap, preserving document ID, 1-indexed page number, and character offsets."*
- **Important Technical Point:** Chunk overlap prevents semantic truncation when a key factoid spans across a split boundary.
- **Possible Question:** *"What happens if a chunk boundary splits an equation or sentence?"*  
  *Answer:* *"The 100-token sliding window overlap ensures that the boundary tokens appear in both chunk $c_i$ and chunk $c_{i+1}$, maintaining contextual continuity."*

---

### Slide 13: Two-Stage Retrieval & Neural Re-ranking
- **Slide Objective:** Detail the mathematical and algorithmic difference between bi-encoders and cross-encoders.
- **What to Show:** Mathematical diagrams of bi-encoder independent vector mapping vs. cross-encoder joint token self-attention.
- **What to Say:**  
  *"This slide highlights our core retrieval innovation. In Stage 1, the bi-encoder maps the query and document independently into vector space. While fast, it cannot capture cross-token interactions. In Stage 2, candidate pairs $(q, c_i)$ are concatenated into sequence `[CLS] q [SEP] c_i [SEP]`. In the cross-encoder, every token in the query directly attends to every token in the candidate passage across all 6 transformer layers. The classification logit is passed through a sigmoid function to obtain calibrated probabilities. Chunks below 0.15 relevance are discarded, and the top 5 chunks are selected."*
- **Important Technical Point:** Bi-encoder complexity is $O(N)$ dot products; cross-encoder complexity is $O(M \cdot L^2)$ self-attention, making the two-stage cascade necessary.
- **Possible Question:** *"Why not run the cross-encoder across all chunks in the entire database?"*  
  *Answer:* *"Evaluating a cross-encoder across thousands of chunks would take several seconds or minutes per query. Over-fetching 15 candidates via vector search restricts cross-encoder execution to just ~133 ms."*

---

### Slide 14: Source Citations & Document Evidence
- **Slide Objective:** Explain how DocuRAG enforces 100% auditable evidence and prevents hallucinated citations.
- **What to Show:** Delimited prompt structure, citation sanitizer regex, Evidence Drawer screenshot, and page preview endpoint.
- **What to Say:**  
  *"To guarantee verifiable answers, DocuRAG wraps context in strict XML-style delimiters, instructing Gemini to cite evidence using markers `[1]`, `[2]`. When Gemini returns an answer, our citation sanitizer verifies every marker against retrieved chunks. If the model cites an out-of-bounds index like `[8]` when only 5 chunks exist, it is stripped. Non-sequential markers are re-indexed. For each citation, the system extracts a 150-character snippet and displays the exact document, page number, and similarity score in the React Evidence Drawer. Clicking a citation opens a rendered visual image of the source PDF page."*
- **Important Technical Point:** Prompt injection defense is built directly into the prompt framing, instructing the LLM that document content is untrusted data and must never be interpreted as instructions.
- **Possible Question:** *"Can the LLM ignore your citation instructions?"*  
  *Answer:* *"If the LLM emits invalid or missing citations, our algorithmic sanitizer catches them deterministically, stripping false indices and falling back to ungrounded safe notices."*

---

### Slide 15: Experimental Evaluation Methodology
- **Slide Objective:** Present the scientific Cranfield evaluation protocol and dataset characteristics.
- **What to Show:** Evaluation corpus table (24 pages across 3 papers), 60-question benchmark taxonomy, and Cranfield IR metric formulas.
- **What to Say:**  
  *"To scientifically evaluate DocuRAG without fabricating numbers, we implemented a Cranfield benchmark suite (`EXP_20261004_065505_60`). We used a 24-page academic corpus across three foundational papers: Vaswani et al. on Transformers, Karpukhin et al. on DPR, and Nogueira & Cho on Re-ranking. We designed a gold-standard dataset of 60 human-verified questions: 54 answerable queries spanning Factoid, Concept, Comparison, Multi-Hop, and Algorithm categories, plus 6 adversarial out-of-domain queries to measure hallucination resistance."*
- **Important Technical Point:** Cranfield methodology isolates retrieval performance by comparing retrieved sets against verified relevance judgments.
- **Possible Question:** *"Why include out-of-domain unanswerable questions?"*  
  *Answer:* *"To evaluate Abstention Accuracy. An enterprise QA system must reliably say 'I cannot answer' when information is absent, rather than hallucinating plausible false facts."*

---

### Slide 16: Empirical Results & Comparative Analysis
- **Slide Objective:** Walk the examiners through the exact empirical gains achieved by cross-encoder re-ranking.
- **What to Show:** The quantitative results table comparing Stage 1 (Vector) vs. Stage 2 (Reranked).
- **What to Say:**  
  *"Here are our actual measured experimental results. Cross-encoder re-ranking improved **Precision@5 by +6.01%**, from 0.2481 to 0.2630. It boosted **Recall@5 by +4.54%**, from 0.9506 to 0.9938. Most importantly, it achieved a **flawless 100.0% Hit Rate@5**, meaning every single answerable question had relevant evidence in its top-5 context. For complex Comparison queries, MRR surged by **+9.76%**, proving that adaptive document balancing works. Finally, Abstention Accuracy was **1.0000**, meaning 100% of out-of-domain queries safely refused to answer."*
- **Important Technical Point:** Precision@5 is bounded near ~0.26 because questions have an average of 1.3 ground-truth chunks ($1.3 / 5 = 0.26$); DocuRAG operates at the theoretical ceiling.
- **Possible Question:** *"Why did factoid MRR show a minor dip from 1.0000 to 0.9500?"*  
  *Answer:* *"Bi-encoders match exact single numerical tokens perfectly at rank 1. The cross-encoder occasionally ranks a broader contextual paragraph at rank 1 and the exact number at rank 2; however, both remain in the top-3 context, and overall Hit Rate is 100%."*

---

### Slide 17: System Verification, Testing & Security
- **Slide Objective:** Demonstrate enterprise software quality, test-driven rigor, and security hardening.
- **What to Show:** Test suite breakdown (119 tests across 17 modules), security mitigations (IDOR, SQLi, XSS, rate limiting).
- **What to Say:**  
  *"DocuRAG has been verified using 119 automated tests across 17 test modules, achieving a 100% pass rate in 56.86 seconds. We hardened the application against critical enterprise vulnerabilities: Insecure Direct Object References are prevented through strict user ID validation on all endpoints; file uploads enforce MIME type and path traversal sanitization; SQL injection is completely prevented via SQLAlchemy parameterization; and rate limiting protects against denial-of-service."*
- **Important Technical Point:** Pytest executes both asynchronous coroutine tests (`pytest-asyncio`) and synchronous algorithmic invariants.
- **Possible Question:** *"How did you test for IDOR vulnerabilities?"*  
  *Answer:* *"We registered User A and User B in automated tests. User A attempted to access, query, and delete documents and chat sessions created by User B; the API strictly returned HTTP 403 or 404."*

---

### Slide 18: Cloud Deployment & Infrastructure
- **Slide Objective:** Present the production deployment topology and cloud-native architecture.
- **What to Show:** Multi-cloud deployment diagram: Vercel, Render, Neon PostgreSQL, AWS S3, and Docker.
- **What to Say:**  
  *"DocuRAG is production-deployed across modern cloud platforms. The React frontend is hosted on Vercel's global Edge CDN with SPA rewrite rules. The FastAPI backend runs on Render as a containerized ASGI service with 4 Uvicorn workers. Transactional data is managed on Neon Serverless PostgreSQL with connection pooling. Documents are stored via pluggable abstractions supporting AWS S3, and ChromaDB manages persistent vector indexing. Container health probes monitor system liveness and readiness."*
- **Important Technical Point:** Pluggable `BaseStorageProvider` enables seamless switching between local disk and AWS S3 without modifying application business logic.
- **Possible Question:** *"How does the frontend handle SPA routing on Vercel?"*  
  *Answer:* *"We configured `vercel.json` and `_redirects` with a rewrite rule routing all paths `/*` to `/index.html` with a 200 status code, allowing React Router to manage deep client-side routes."*

---

### Slide 19: Limitations & Future Work
- **Slide Objective:** Exhibit mature academic self-awareness by discussing real constraints and research trajectories.
- **What to Show:** Bullet points covering CPU latency scaling, memory footprints, multi-hop reasoning, and future research paths.
- **What to Say:**  
  *"In accordance with academic rigor, we acknowledge current system limitations: first, CPU cross-encoder latency scales linearly with candidate pool size, bounding candidate pools to 15–20 chunks on CPU hardware; second, keeping dual transformer models in RAM requires ~450 MB resident memory; third, complex multi-hop questions requiring iterative reasoning across disjoint sections cannot execute autonomous sub-queries. In future work, we plan to implement ColBERT token-level late interaction, Graph-RAG for relational knowledge graph traversal, and domain-specific cross-encoder fine-tuning."*
- **Important Technical Point:** ColBERT's MaxSim operator achieves cross-encoder quality while pre-computing token vectors, avoiding $O(M \cdot L^2)$ joint attention at query time.
- **Possible Question:** *"What is Graph-RAG?"*  
  *Answer:* *"Graph-RAG extracts entity-relationship triples from documents into a knowledge graph. Queries perform graph traversals across entities, enabling multi-hop reasoning that vector search cannot achieve."*

---

### Slide 20: Conclusion & Summary of Achievements
- **Slide Objective:** Deliver a confident, memorable concluding summary of the project's success.
- **What to Show:** High-level summary of deliverables: 100% Hit Rate@5, zero hallucination, 119 passing tests, full documentation suite.
- **What to Say:**  
  *"In conclusion, DocuRAG bridges the gap between academic NLP research and enterprise software engineering. By pairing fast vector retrieval with deep neural re-ranking, adaptive multi-document balancing, and deterministic citation sanitization, DocuRAG eliminates the critical vulnerabilities of naive RAG. We achieved a 100% Hit Rate@5, complete hallucination resistance, 100% test coverage across 119 tests, and delivered a complete MCA dissertation and research paper. Thank you for your time and guidance. I now welcome your questions."*
- **Important Technical Point:** The project is fully committed to Git with a clean working tree and verified reproducibility.
- **Possible Question:** *"Are you ready for the live demonstration?"*  
  *Answer:* *"Yes, respected examiners, the application is active and ready for live demonstration."*
