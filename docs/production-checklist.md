# DocuRAG Production Readiness & Verification Checklist

This document provides a systematic verification matrix for certifying DocuRAG in a production cloud environment.

---

## 1. Authentication & Session Security

- [x] **Registration**: New user registration validates email uniqueness and enforces minimum 6-character passwords.
- [x] **Password Hashing**: Passwords stored as salted bcrypt hashes; plaintext passwords never touch the database or logs.
- [x] **JWT Generation**: Bearer access tokens signed with HMAC-SHA256 using server-side `JWT_SECRET_KEY`.
- [x] **Token Expiration**: Enforces configurable TTL (`ACCESS_TOKEN_EXPIRE_MINUTES=1440`).
- [x] **Protected Routes**: Unauthenticated requests to `/documents`, `/chat`, `/evaluation` cleanly reject with HTTP 401 Unauthorized.
- [x] **Client-Side Auth Interceptor**: Axios automatically handles 401 responses by clearing expired tokens and redirecting to `/login`.
- [x] **User Isolation (Multi-Tenancy)**: Strict SQL filtering ensures User A cannot view, retrieve, or query User B's documents or sessions.
- [x] **Server-Side IDOR Defense**: Direct URL attempts to view or delete another user's document ID or session ID return HTTP 404 Not Found.

---

## 2. Document Ingestion & Storage

- [x] **File Extension Validation**: Rejects non-PDF uploads with HTTP 400 Bad Request.
- [x] **MIME Type Validation**: Verifies `application/pdf` Content-Type header.
- [x] **File Size Enforcement**: Blocks uploads exceeding `MAX_FILE_SIZE_MB` (default 25 MB) before memory exhaustion.
- [x] **Path Traversal Defense**: Sanitizes user-provided filenames, strips `..` sequences, and verifies resolved storage path stays within `upload_dir`.
- [x] **Corrupted / Empty PDF Rejection**: Intercepts 0-byte or corrupted PDF files and returns clean user-friendly HTTP 400 errors.
- [x] **Encrypted PDF Rejection**: Gracefully detects password-protected PDFs and returns clean error without crashing.
- [x] **Storage Abstraction**: Supports both persistent volume mounts and S3-compatible cloud object storage (Cloudflare R2 / AWS S3).
- [x] **Page Serving Endpoint**: Authenticated endpoint `GET /api/documents/{id}/pages/{page}` serves text content for interactive citation drawer.

---

## 3. Vector Database & RAG Pipeline

- [x] **ChromaDB Persistence**: Indexes stored in persistent directory or remote Chroma server (`CHROMA_HOST`), surviving container restarts.
- [x] **Dense Embeddings**: `all-MiniLM-L6-v2` loaded as application singleton to eliminate repetitive model loading latency.
- [x] **Multi-Document Vector Isolation**: ChromaDB queries apply strict `{"user_id": current_user.id}` metadata filtering.
- [x] **Document Balancing**: Multi-document queries balance chunk candidate retrieval across all selected documents.
- [x] **Cross-Encoder Reranking**: `cross-encoder/ms-marco-MiniLM-L-6-v2` reranks candidate chunks using joint query-context attention.
- [x] **Prompt Injection Defense**: Retrieved chunks demarcated as UNTRUSTED DATA; model strictly refuses commands embedded within documents.
- [x] **Grounded Answering**: Model produces factual answers strictly supported by retrieved excerpts.
- [x] **Abstention on Out-of-Scope**: Accurately outputs safe fallback message when evidence is insufficient.
- [x] **Deterministic Citations**: Inline citations `[1]`, `[2]` mapped directly to source document names and 1-indexed page numbers.
- [x] **Citation Sanitization**: Strips hallucinated citation brackets referencing non-existent sources.

---

## 4. Chat History & Conversation Memory

- [x] **Persistent Sessions**: Chat sessions stored in database with timestamps and document bindings.
- [x] **Multi-Turn Context**: LLM resolves conversational references (e.g. "it", "the first paper") using recent conversation turns.
- [x] **Session Title Auto-Generation**: Automatically updates session title from initial placeholder to the first user question.
- [x] **Soft-Tombstoning**: Reopened sessions with deleted documents display an advisory badge without crashing.

---

## 5. Research Evaluation Suite & Dashboard

- [x] **Evaluation Dataset**: 24-page academic corpus with 60 verified ground-truth questions and golden page annotations.
- [x] **Automated Benchmark Runner**: Executes dual-stage evaluation (Standard Vector vs Cross-Encoder Reranked).
- [x] **Standard IR Metrics**: Calculates empirical Precision@K, Recall@K, Hit Rate@K, and Mean Reciprocal Rank (MRR).
- [x] **Interactive Dashboard**: Modern React interface with Recharts charts, latency profiling, error taxonomy, and CSV/JSON export.

---

## 6. Production Infrastructure & Operations

- [x] **Zero Hardcoded Localhost**: Frontend API base URL driven by `VITE_API_BASE_URL`.
- [x] **Strict CORS Configuration**: Configurable `CORS_ORIGINS` restricts access to authorized frontend domains.
- [x] **Dynamic Port Binding**: Backend listens to `$PORT` environment variable provided by cloud hosts.
- [x] **Rate Limiting**: Sliding-window rate limiter prevents abuse of generative and upload endpoints (60 req/min).
- [x] **Security Headers**: Responses include `nosniff`, `DENY` frame options, and strict referrer policy.
- [x] **Distributed Request Tracing**: Injects unique `X-Request-ID` and `X-Response-Time-Ms` in all responses.
- [x] **Health Check Endpoints**: `/api/health`, `/api/health/live`, `/api/health/ready` operational.
- [x] **Clean SPA Routing**: `vercel.json`, `_redirects`, and `nginx.conf` prevent 404 errors on direct navigation.
- [x] **No Committed Secrets**: Repository scanned clean of API keys, passwords, and tokens.
- [x] **Mobile Responsiveness**: UI adapts cleanly to small screens (Android Chrome / iPhone Safari).
