# REST API Specification

All API endpoints are prefixed with `/api`.
Authenticated endpoints require a Bearer token in the `Authorization` header:
`Authorization: Bearer <jwt_token>`

---

## 1. Authentication Endpoints

### POST `/api/auth/register`
Creates a new user account.
- **Request Body:**
```json
{
  "name": "Alex Student",
  "email": "alex@university.edu",
  "password": "SecurePassword123!"
}
```
- **Response (201 Created):**
```json
{
  "id": 1,
  "name": "Alex Student",
  "email": "alex@university.edu",
  "created_at": "2026-10-03T21:00:00Z"
}
```

### POST `/api/auth/login`
Authenticates credentials and returns a JWT access token.
- **Request Body:** (JSON or form-data)
```json
{
  "email": "alex@university.edu",
  "password": "SecurePassword123!"
}
```
- **Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Alex Student",
    "email": "alex@university.edu"
  }
}
```

### GET `/api/auth/me`
Retrieves currently logged-in user profile.

---

## 2. Document Management Endpoints

### POST `/api/documents/upload`
Uploads and enqueues a PDF document for parsing, chunking, and embedding.
- **Request:** `multipart/form-data` with field `file`.
- **Response (202 Accepted):**
```json
{
  "id": 12,
  "filename": "deep_residual_learning.pdf",
  "status": "PROCESSING",
  "page_count": 0,
  "chunk_count": 0,
  "file_size": 1048576,
  "created_at": "2026-10-03T21:05:00Z"
}
```

### GET `/api/documents`
Lists all documents belonging to the authenticated user.

### GET `/api/documents/{id}`
Returns status and metadata for a specific document.

### DELETE `/api/documents/{id}`
Deletes the document file, database records, and all corresponding embeddings in ChromaDB.

---

## 3. Chat & Question Answering Endpoints

### POST `/api/chat/sessions`
Creates a new conversation session.
- **Request Body:**
```json
{
  "title": "Discussion on ResNet Architecture"
}
```

### GET `/api/chat/sessions`
Lists all user chat sessions.

### GET `/api/chat/sessions/{id}`
Returns session details with full message history and citations.

### POST `/api/chat/ask`
Submits a question to the RAG engine.
- **Request Body:**
```json
{
  "session_id": 4,
  "question": "What is the degradation problem addressed by residual learning?",
  "document_ids": [12],
  "top_k": 5,
  "use_reranker": false
}
```
- **Response (200 OK):**
```json
{
  "session_id": 4,
  "question": "What is the degradation problem addressed by residual learning?",
  "answer": "The degradation problem refers to the phenomenon where, as network depth increases, accuracy saturates and then degrades rapidly...",
  "sources": [
    {
      "document_id": 12,
      "document_name": "deep_residual_learning.pdf",
      "page_number": 2,
      "chunk_id": "doc12_p2_c1",
      "similarity_score": 0.884,
      "snippet": "With the network depth increasing, accuracy gets saturated and then degrades rapidly..."
    }
  ],
  "latency_ms": 782,
  "retrieval_count": 5
}
```

---

## 4. Academic Evaluation Endpoints

### POST `/api/evaluation/run`
Executes retrieval benchmarks across 3 approaches (BM25 Keyword, Semantic Vector, Semantic + Reranking).
- **Request Body:**
```json
{
  "dataset_path": "evaluation/evaluation_questions.csv",
  "top_k": 5
}
```

### GET `/api/evaluation/results`
Returns historical evaluation runs, comparative IR metrics, and latency charts.
