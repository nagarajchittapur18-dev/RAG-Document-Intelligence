# DocuRAG — Live Demonstration Script & Failure Recovery Plan
**Academic Title:** *AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation*  
**Purpose:** Step-by-Step Live Demonstration Protocol for External Examiners & Faculty  

---

## 1. Live Demonstration Overview

This document provides an exact, reproducible 20-step demonstration sequence. The live demo showcases document ingestion, text sanitization, single-document factual Q&A, interactive citations, on-demand PDF page rendering, multi-turn conversational memory, multi-document comparative Q&A with fair balancing, live evaluation dashboard inspection, and multi-tenant session persistence.

---

## 2. Step-by-Step Demonstration Sequence (20 Steps)

### Step 1: Access Application URL
- **Action**: Open web browser (Chrome/Firefox/Edge) and navigate to the DocuRAG application URL:
  - Production: `https://docurag.vercel.app` (or local instance: `http://localhost:5173`)
- **Speech**: *"Here is the production deployment of DocuRAG. The client is a responsive React 18 single-page application communicating over HTTPS with our FastAPI backend on Render."*

### Step 2: User Registration & Authentication
- **Action**: Click **Register**, enter an academic email (e.g., `examiner@university.edu`), create an 8+ character password, and click Submit.
- **Speech**: *"DocuRAG is multi-tenant. Passwords are cryptographically salted and hashed using bcrypt on the backend, and authentication issues an industry-standard signed JWT bearer token with a 24-hour expiration."*

### Step 3: Open Document Management Dashboard
- **Action**: The user is redirected to the main dashboard (`/documents`).
- **Speech**: *"This is the document management view. It lists the user's uploaded documents, page counts, chunk counts, and processing statuses. Notice that because I just registered as a new user, the document repository is empty, demonstrating tenant isolation."*

### Step 4: Upload First Academic PDF
- **Action**: Click **Upload Document**, drag and drop `Attention_Is_All_You_Need.pdf` (15 pages).
- **Speech**: *"I am uploading the seminal 15-page Transformer research paper by Vaswani et al. The backend immediately inspects the MIME type and magic bytes, verifying it is an unencrypted PDF."*

### Step 5: Observe Asynchronous Ingestion & Processing
- **Action**: Observe the upload progress indicator transitioning from *Uploading* to *Processing* to *Ready*.
- **Speech**: *"During this brief processing step, PyMuPDF extracts the text page-by-page, reconnects broken line wraps, and applies recursive character splitting to create 500-token chunks with 100-token overlap. Chunks are converted into 384-dimensional dense vectors using `all-MiniLM-L6-v2` and indexed into ChromaDB with metadata tags."*

### Step 6: Open Chat Session & Inspect Document Details
- **Action**: Click on the uploaded document card to enter the Chat Interface. Point out the document metadata badge (15 pages, 42 chunks).
- **Speech**: *"Here we enter the conversational Q&A interface. Notice the document badge confirms that all 15 pages and 42 text chunks have been successfully indexed."*

### Step 7: Ask a Specific Factual Question (Single-Document Mode)
- **Action**: In the chat input box, submit:  
  `"What is the dimensionality d_model of the base Transformer model?"`
- **Speech**: *"I am asking a precise architectural question. The query is embedded and sent to ChromaDB. Stage 1 over-fetches 15 candidate chunks; Stage 2 cross-encoder re-ranks them, and Gemini 2.5 Flash synthesizes the answer in about 1.4 seconds."*

### Step 8: Observe Grounded Answer & Inline Citations
- **Action**: Point out the generated response:  
  *"The dimensionality of the base Transformer architecture is $d_{\text{model}} = 512$ [1]."*
- **Speech**: *"Notice the generated answer is concise and factual. Most importantly, it includes an inline citation marker [1]."*

### Step 9: Expand the Interactive Evidence Drawer
- **Action**: Click on the inline citation badge `[1]`. The slide-out Evidence Drawer opens from the right.
- **Speech**: *"When the user clicks the citation marker, DocuRAG opens our interactive Evidence Drawer. It displays the exact text snippet extracted from the document, the filename, the 1-indexed page number (Page 3), the vector similarity score (0.84), and the cross-encoder re-rank score (0.91)."*

### Step 10: View On-Demand PDF Page Rendering
- **Action**: Click **View Page Preview** in the Evidence Drawer. A high-resolution image of Page 3 from the PDF renders in the modal.
- **Speech**: *"To ensure 100% human auditability, the user does not have to trust the text snippet alone. The backend endpoint `GET /api/documents/{id}/pages/3` renders the actual visual PDF page, allowing examiners to inspect the original publication."*

### Step 11: Ask a Multi-Turn Follow-Up Question (Pronoun Coreference)
- **Action**: Submit the follow-up message:  
  `"How many attention heads does it use?"`
- **Speech**: *"Notice I used the pronoun 'it'. Standard RAG fails on pronouns because vector search for 'it' yields poor similarity. DocuRAG's query rewriter analyzes the conversation history and reformulates the query into 'How many attention heads does the base Transformer model use?' before querying ChromaDB."*
- **Action**: Observe answer: *"The base model uses $h = 8$ parallel attention heads [1]."*

### Step 12: Create a New Chat Session
- **Action**: Click **New Chat** in the left sidebar.
- **Speech**: *"We can organize research into multiple isolated chat sessions. Notice the previous session automatically autogenerated a descriptive title: 'Transformer Dimensionality and Attention Heads'."*

### Step 13: Upload Second Academic Document
- **Action**: Navigate to `/documents` and upload the second test paper: `DPR_Open_Domain_QA.pdf` (Karpukhin et al., 2020, 5 pages).
- **Speech**: *"Now I am uploading a second paper on Dense Passage Retrieval. The ingestion pipeline chunks and vectors this document independently into ChromaDB."*

### Step 14: Execute a Multi-Document Comparative Query
- **Action**: In the chat session, select both documents (or choose *All Documents* mode) and ask:  
  `"Compare Dense Passage Retrieval with the Transformer architecture regarding their primary objectives."`
- **Speech**: *"This demonstrates our multi-document RAG capabilities. In naive RAG, the longer 15-page Transformer paper would monopolize all retrieved chunks. DocuRAG's adaptive document balancing algorithm partitions candidates equally across both papers, ensuring balanced representation."*
- **Action**: Point out the answer citing both `[1]` (Attention is All You Need) and `[2]` (DPR).

### Step 15: Open the Academic Evaluation Dashboard
- **Action**: Navigate to `/evaluation` in the navigation header.
- **Speech**: *"DocuRAG includes a built-in research evaluation suite reading directly from our empirical Cranfield benchmark results (`summary.json`)."*

### Step 16: Inspect Retrieval KPI Cards & Cutoff Metrics
- **Action**: Highlight the KPI cards: Precision@5 (0.2630), Recall@5 (0.9938), Hit Rate@5 (1.0000), MRR (0.9188), and Abstention Accuracy (1.0000).
- **Speech**: *"These are the actual experimental results from our 60-question benchmark. Cross-encoder re-ranking achieved a flawless 100% Hit Rate at Top-5 and 99.38% Recall, capturing almost all relevant evidence across the corpus."*

### Step 17: Inspect Comparative Re-ranking Charts & Latency Profiles
- **Action**: Scroll to the Chart.js comparative bar charts showing Vector vs. Re-ranked Precision, Recall, and Hit Rate across $K \in \{1, 3, 5, 10\}$, and the latency distribution chart.
- **Speech**: *"This chart clearly illustrates the gain: Re-ranking provides a +6.01% gain in Precision@5 and a +4.54% gain in Recall@5. The median re-ranking latency is just 133 milliseconds on CPU."*

### Step 18: Logout to Demonstrate Authentication Security
- **Action**: Click **User Profile** $\rightarrow$ **Logout**. The client clears the JWT token from localStorage and redirects to `/login`.
- **Speech**: *"Logging out purges the JWT bearer token from client state, ensuring session termination."*

### Step 19: Log Back In to Demonstrate State Persistence
- **Action**: Log back in using the credentials from Step 2.
- **Speech**: *"When the user logs back in, FastAPI verifies the credentials against PostgreSQL and issues a new token."*

### Step 20: Verify Chat History & Citation Provenance Restoration
- **Action**: Click on the previous chat session. Observe all past messages, user queries, assistant answers, and clickable citation markers restored intact.
- **Speech**: *"All conversation messages, autogenerated session titles, and citation provenance are fully restored from our relational database tables (`chat_messages` and `message_citations`). This completes our live demonstration."*

---

## 3. Demo Failure Recovery & Contingency Plan

During a live viva voce examination, unexpected network, API, or hardware issues may arise. Follow this structured contingency protocol:

### Contingency 1: Google Gemini API Quota or Network Timeout
- **Symptom**: Answer takes >10 seconds or returns HTTP 503 / 429.
- **Immediate Action**:
  1. Do NOT panic or refresh repeatedly.
  2. Explain the architecture calmly:  
     *"Examiners, the external Google Gemini API is experiencing temporary network latency or rate limiting. Notice, however, that our backend retrieval pipeline completed in 145 ms, and our candidate chunks were successfully re-ranked."*
  3. Navigate to `/evaluation` and show the pre-computed, stored evaluation benchmark results (`summary.json`) that record the exact outputs across all 60 queries.

### Contingency 2: Campus Wi-Fi / Internet Disconnection
- **Symptom**: Browser shows network disconnected.
- **Immediate Action**:
  1. Switch immediately to the pre-configured local development server:
     - Frontend: `http://localhost:5173`
     - Backend: `http://localhost:8000`
  2. Local server uses SQLite and local ChromaDB persistence, which requires zero internet for vector retrieval and re-ranking.
  3. If Gemini generation requires internet, connect phone via USB tethering.

### Contingency 3: PDF Processing / PyMuPDF Error on a New File
- **Symptom**: Uploading an unvetted PDF raises an error.
- **Immediate Action**:
  1. Use only the **prepared test PDFs**:
     - `Attention_Is_All_You_Need.pdf`
     - `DPR_Open_Domain_QA.pdf`
     - `Passage_Reranking_BERT.pdf`
  2. If an examiner insists on uploading their own PDF and it fails, explain:  
     *"DocuRAG proactively validates PDFs for text layers. This document is a scanned image without an embedded OCR text layer, so our system safely raised `ScannedPDFError` rather than indexing silent empty chunks."*

### Contingency 4: Relational Database Connection Issue
- **Symptom**: Neon PostgreSQL connection timeout.
- **Immediate Action**:
  1. The backend automatically supports SQLite fallback.
  2. In `backend/.env`, set `DATABASE_URL=sqlite:///./docurag.db` and restart Uvicorn (`uvicorn app.main:app --reload`). The application will resume in 3 seconds.

### Contingency 5: Total Hardware / Browser Freeze
- **Symptom**: Laptop freezes or browser crashes.
- **Immediate Action**:
  1. Keep an offline PDF copy of [`docs/results-analysis.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/results-analysis.md) and [`docs/project-report.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/project-report.md) on a flash drive or tablet.
  2. Present the empirical evaluation charts, architecture diagrams, and test suite results directly from the documentation.
  3. **Never fabricate or fake a live operation.** Transparency and architectural mastery impress examiners far more than an artificial facade.
