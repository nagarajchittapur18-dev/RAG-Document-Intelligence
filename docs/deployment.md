# DocuRAG Production Deployment Guide

This guide details the complete, step-by-step production deployment process for **DocuRAG (RAGMate)**.

---

## 1. Cloud Architecture Overview

The recommended production deployment topology separates static frontend assets, containerized FastAPI compute, managed PostgreSQL persistence, persistent ChromaDB vector storage, and S3-compatible document storage:

| Component | Recommended Production Platform | Free / Low-Cost Tier Support | Alternative Options |
|---|---|---|---|
| **Frontend SPA** | **Vercel** | Yes (Hobby tier: free SSL, global CDN) | Netlify, Cloudflare Pages, Nginx |
| **Backend API** | **Render** or **Railway** | Yes (Render Web Service / Railway Starter) | Fly.io, AWS ECS, Google Cloud Run |
| **Relational Database** | **Neon** or **Supabase** | Yes (Serverless Postgres with SSL: free) | Render PostgreSQL, Railway Postgres |
| **Document Storage** | **Cloudflare R2** or **Persistent Disk** | Yes (R2: 10GB free, $0 egress / Mount Disk) | AWS S3, Supabase Storage, MinIO |
| **Vector Database** | **Persistent Volume** (`/chroma_data`) | Yes (Render Disk / Railway Volume) | Remote Chroma server, Chroma Cloud |
| **Generative LLM** | **Google Gemini API** | Yes (Google AI Studio free tier) | Gemini 1.5 Flash / Pro |

---

## 2. Step 1: Managed PostgreSQL Database Setup

DocuRAG supports PostgreSQL natively via SQLAlchemy with connection pooling and the `psycopg` v3 driver.

### Option A: Neon Serverless PostgreSQL (Recommended)
1. Sign in to [Neon Console](https://console.neon.tech/).
2. Create a new project: `docurag-production`.
3. In the project dashboard, copy the pooled connection string:
   ```text
   postgresql+psycopg://username:password@ep-xyz-pooler.region.neon.tech/neondb?sslmode=require
   ```
4. *Note*: If Neon gives a connection string starting with `postgres://`, DocuRAG automatically normalizes it to `postgresql+psycopg://` upon initialization.

### Option B: Supabase PostgreSQL
1. Sign in to [Supabase Console](https://supabase.com/dashboard).
2. Create a new project: `docurag-production`.
3. Navigate to **Project Settings** → **Database** → **Connection String** → **URI**.
4. Use the connection string with `sslmode=require`.

### Database Schema Initialization
Run the zero-downtime migration and table verification script from the backend:
```bash
# Set your production database URL
export DATABASE_URL="postgresql+psycopg://user:password@host/dbname?sslmode=require"

# Execute the database schema initialization script
python -m app.db.init_db
```
This automatically provisions all required tables (`users`, `documents`, `chat_sessions`, `messages`, `chat_session_documents`) and performance indexes.

---

## 3. Step 2: Document Storage Configuration

DocuRAG implements the `BaseStorageProvider` abstraction, supporting persistent local storage and S3-compatible cloud object storage.

### Option A: Persistent Cloud Disk (Render / Railway / Fly.io)
If deploying backend on a container platform that supports persistent disks:
- Set `STORAGE_PROVIDER=local`
- Set `UPLOAD_DIRECTORY=/app/uploads`
- Mount a persistent disk volume to `/app/uploads` (minimum size: 2 GB).

### Option B: S3-Compatible Cloud Object Storage (Cloudflare R2 / AWS S3)
For ephemeral container platforms without disk persistence:
1. Create a bucket named `docurag-documents` in Cloudflare R2 or AWS S3.
2. Generate Access Key ID and Secret Access Key.
3. Configure backend environment variables:
   ```env
   STORAGE_PROVIDER=s3
   STORAGE_BUCKET=docurag-documents
   STORAGE_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
   STORAGE_REGION=auto
   STORAGE_ACCESS_KEY=<your_access_key>
   STORAGE_SECRET_KEY=<your_secret_key>
   ```

---

## 4. Step 3: Backend Deployment (FastAPI on Render)

### 1. Create Web Service on Render
1. Connect your GitHub repository to [Render Dashboard](https://dashboard.render.com/).
2. Click **New** → **Web Service**.
3. Select your repository.
4. Set the following build and run parameters:
   - **Name**: `docurag-backend`
   - **Region**: Closest to your users (e.g. `Frankfurt` or `Oregon`)
   - **Branch**: `master`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --no-cache-dir -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`

### 2. Configure Persistent Disk (for ChromaDB & Local Files)
1. In the Render Web Service settings, navigate to **Disks**.
2. Click **Add Disk**:
   - **Name**: `docurag-data`
   - **Mount Path**: `/app/data`
   - **Size**: `2 GB`
3. Update environment variables to store Chroma and uploads on the mounted disk:
   - `CHROMA_PERSIST_DIRECTORY=/app/data/chroma_data`
   - `UPLOAD_DIRECTORY=/app/data/uploads`

### 3. Set Backend Environment Variables
In the Render **Environment** tab, add:

| Variable | Example Value | Description |
|---|---|---|
| `ENVIRONMENT` | `production` | Deployment mode |
| `DATABASE_URL` | `postgresql+psycopg://...` | Connection string to Neon / Supabase |
| `GEMINI_API_KEY` | `AIzaSy...` | Google AI Studio Gemini API key |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Active generative LLM |
| `JWT_SECRET_KEY` | `e3b0c44298fc1c149...` | 32+ character random secret (`openssl rand -hex 32`) |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Session token TTL (24 hours) |
| `CORS_ORIGINS` | `https://docurag.vercel.app` | Allowed frontend origin URL |
| `CHROMA_PERSIST_DIRECTORY` | `/app/data/chroma_data` | Persistent path for vector store |
| `UPLOAD_DIRECTORY` | `/app/data/uploads` | Persistent path for documents |
| `RERANKER_ENABLED` | `true` | Enables Cross-Encoder reranking |

4. Click **Deploy Web Service**.
5. Once deployed, test the health endpoint:
   ```bash
   curl -i https://docurag-backend.onrender.com/api/health
   ```
   Verify response is `{"status": "ok", "database": "healthy", "vector_store": "healthy"}`.

---

## 5. Step 4: Frontend Deployment (React / Vite on Vercel)

### 1. Configure Vercel Project
1. Log in to [Vercel](https://vercel.com/) (CLI or Web Dashboard).
2. Click **Add New...** → **Project**.
3. Import your GitHub repository (`RAGMate` / `DocuRAG`).
4. Configure Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### 2. Configure Frontend Environment Variable
In the **Environment Variables** section of the Vercel project, add:

| Variable | Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `https://docurag-backend.onrender.com/api` | Public backend API URL |

3. Click **Deploy**.
4. Vercel automatically deploys the frontend and generates a public HTTPS URL (e.g. `https://docurag.vercel.app`).
5. `frontend/vercel.json` automatically manages client-side SPA routing rewrites so direct navigation to `/dashboard`, `/chat`, `/documents`, and `/evaluation` never returns 404 errors.

---

## 6. Step 5: Connecting Frontend and Backend (CORS & Verification)

1. Return to the **Backend Web Service** (Render / Railway).
2. Update the `CORS_ORIGINS` environment variable to include your actual Vercel URL:
   ```env
   CORS_ORIGINS=https://docurag.vercel.app,http://localhost:5173
   ```
3. Trigger a redeploy of the backend so the updated CORS policy takes effect.

---

## 7. Step 6: Docker / Local Production Stack

To run the complete production stack on a single Linux / Cloud VM (AWS EC2, DigitalOcean Droplet, Hetzner Cloud):

```bash
# 1. Clone repository
git clone https://github.com/nagarajchittapur/RAGMate.git
cd RAGMate

# 2. Configure production .env
cp .env.example .env
nano .env  # Input your GEMINI_API_KEY and generate JWT_SECRET_KEY

# 3. Launch complete stack via Docker Compose
docker compose up -d --build

# 4. Verify running services
docker compose ps
docker compose logs -f
```

The stack exposes:
- **Frontend SPA**: `http://<your-server-ip>:5173` (or port 80 via Nginx reverse proxy)
- **Backend API**: `http://<your-server-ip>:8000`
- **Swagger Documentation**: `http://<your-server-ip>:8000/docs`

---

## 8. Post-Deployment Smoke Test Checklist

Execute this smoke test sequence from an external browser / mobile phone:

1. **SPA Routing**: Navigate to `/register` directly in the browser bar. Verify the page renders without 404.
2. **Registration**: Create an account with a test email (`tester@university.edu`).
3. **Authentication**: Verify redirection to `/dashboard` upon registration/login.
4. **Document Upload**: Upload a multi-page PDF document (e.g. academic paper).
5. **Processing**: Observe status transitioning to `completed` with correct page and chunk counts.
6. **Chat Query**: Ask a factual question. Verify the answer includes grounded inline citations (`[1]`).
7. **Evidence Inspection**: Click on citation badge `[1]`. Verify the interactive evidence drawer opens and highlights the source passage.
8. **Chat History**: Refresh browser. Verify previous conversation sessions and messages persist.
9. **Evaluation Dashboard**: Navigate to `/evaluation`. Verify the research evaluation metrics (P@K, MRR, Hit Rate) display accurately.
10. **Logout**: Click Logout and verify redirection to `/login`.
