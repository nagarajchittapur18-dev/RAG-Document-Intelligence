# DocuRAG Production Troubleshooting & Operational Guide

This guide details common operational and deployment issues, their root causes, and verified resolution steps.

---

## 1. CORS (Cross-Origin Resource Sharing) Errors

### Symptoms
- Browser console displays:
  ```text
  Access to XMLHttpRequest at 'https://api.docurag.com/api/auth/login' from origin 'https://docurag.vercel.app' has been blocked by CORS policy.
  ```

### Root Cause
- The backend's `CORS_ORIGINS` setting does not include the exact protocol, domain, or port of the frontend client.

### Resolution
1. Inspect the origin header sent by the browser in DevTools Network tab.
2. Ensure `CORS_ORIGINS` on the backend contains the exact origin URL without trailing slashes:
   ```env
   CORS_ORIGINS=https://docurag.vercel.app,http://localhost:5173
   ```
3. If using multiple subdomains or preview deployments on Vercel:
   ```env
   CORS_ORIGINS=https://docurag.vercel.app,https://docurag-preview.vercel.app
   ```
4. Redeploy or restart the FastAPI backend service.

---

## 2. Database Connection Failure (PostgreSQL)

### Symptoms
- Backend startup logs:
  ```text
  sqlalchemy.exc.OperationalError: connection to server at "ep-xyz.region.neon.tech" failed: Connection refused
  ```
- `/api/health` reports `"database": "unhealthy"`.

### Root Cause
- Incorrect connection string, missing `sslmode=require`, or network egress blocking.

### Resolution
1. Verify the `DATABASE_URL` format. In SQLAlchemy 2.0 with `psycopg` v3, the recommended scheme is:
   ```env
   DATABASE_URL=postgresql+psycopg://username:password@ep-host.region.neon.tech/neondb?sslmode=require
   ```
2. If the provider uses the legacy `postgres://` prefix, DocuRAG automatically normalizes it, but ensure credentials and hostname are correct.
3. Test connectivity directly using the database initialization script:
   ```bash
   python -m app.db.init_db
   ```
4. Verify whether your database provider enforces IP whitelisting.

---

## 3. Google Gemini API Failures (Quota / Authentication)

### Symptoms
- Chat response shows:
  ```text
  Error communicating with AI service: 429 Resource has been exhausted (e.g. check quota).
  ```
  or:
  ```text
  GEMINI_API_KEY is not configured on the server.
  ```

### Root Cause
- Missing `GEMINI_API_KEY`, expired API key, or hitting free-tier RPM (Requests Per Minute) limits.

### Resolution
1. Verify `GEMINI_API_KEY` is set in the cloud hosting provider's environment settings.
2. In Google AI Studio, ensure the active project has the Generative Language API enabled.
3. DocuRAG automatically implements resilient fallback across candidate models:
   - Primary: `gemini-3.1-flash-lite`
   - Secondary: `gemini-3.5-flash-lite`
   - Tertiary: `gemini-3.5-flash`
4. For high-traffic demonstrations, consider upgrading the Gemini project from free tier to pay-as-you-go.

---

## 4. ChromaDB Storage Disappearance After Container Restart

### Symptoms
- Previously uploaded documents cannot be retrieved for questions after a cloud server restart or deployment.
- `/api/health` indicates `0 indexed chunks`.

### Root Cause
- ChromaDB is storing vector embeddings on an ephemeral container filesystem (e.g. default `/chroma_data` without a persistent volume).

### Resolution
1. **Persistent Cloud Volume (Recommended)**:
   - In Render, Railway, or Fly.io, attach a persistent disk (e.g. 2 GB) mounted to `/app/data`.
   - Configure:
     ```env
     CHROMA_PERSIST_DIRECTORY=/app/data/chroma_data
     UPLOAD_DIRECTORY=/app/data/uploads
     ```
2. **Remote Chroma Server**:
   - Deploy a standalone Chroma container or use Chroma Cloud.
   - Configure:
     ```env
     CHROMA_HOST=chroma.internal
     CHROMA_PORT=8000
     ```

---

## 5. Single Page Application (SPA) 404 on Direct Navigation

### Symptoms
- Navigating to `https://docurag.vercel.app/` works, but refreshing while on `https://docurag.vercel.app/dashboard` or `/chat` displays:
  ```text
  404 Not Found
  ```

### Root Cause
- The static web host tries to find a file matching `/dashboard/index.html` on disk instead of routing the request to `/index.html` for client-side React Router handling.

### Resolution
- **For Vercel**: Ensure `frontend/vercel.json` exists with rewrites:
  ```json
  {
    "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
  }
  ```
- **For Netlify**: Ensure `frontend/public/_redirects` contains:
  ```text
  /*    /index.html   200
  ```
- **For Nginx**: Ensure `frontend/nginx.conf` has:
  ```nginx
  location / {
      try_files $uri $uri/ /index.html;
  }
  ```

---

## 6. PDF Upload Failure or Size Limit Exceeded

### Symptoms
- Uploading a PDF returns:
  ```text
  File size (28.40 MB) exceeds maximum allowed size (25 MB).
  ```
  or returns `413 Request Entity Too Large` from a reverse proxy.

### Root Cause
- Either the file exceeds `MAX_FILE_SIZE_MB`, or an upstream Nginx / Cloudflare proxy has a default 1MB/10MB upload limit.

### Resolution
1. To increase allowed file size in DocuRAG:
   ```env
   MAX_FILE_SIZE_MB=50
   ```
2. If using Nginx as a reverse proxy, add to `nginx.conf`:
   ```nginx
   client_max_body_size 50M;
   ```
3. For Cloudflare proxy, ensure file uploads do not exceed the 100MB free-tier upload ceiling.

---

## 7. Memory Exhaustion During Reranking or Model Loading

### Symptoms
- Container suddenly exits with `Killed` or `OOMKilled` (Exit code 137).

### Root Cause
- PyTorch and HuggingFace SentenceTransformer models (`all-MiniLM-L6-v2`, `ms-marco-MiniLM-L-6-v2`) require approximately 350MB–500MB of RAM. If running multiple Uvicorn workers on a 512MB RAM free tier, RAM may be exhausted.

### Resolution
1. Configure Uvicorn to run with a single worker:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
   ```
2. If memory is constrained, you can temporarily disable the Cross-Encoder reranker to reduce RAM consumption:
   ```env
   RERANKER_ENABLED=false
   ```
   The system will automatically fall back to pure Bi-Encoder vector retrieval.
