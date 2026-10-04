import logging
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.evaluation import router as evaluation_router
from app.config import settings
from app.services.document_store import DatabaseManager
from app.services.vector_store import VectorStore
from app.utils.rate_limiter import rate_limiter

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ragmate")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing RAGMate / DocuRAG Intelligent Document QA Backend...")
    logger.info("Active Embedding Model: %s", settings.EMBEDDING_MODEL)
    logger.info("ChromaDB Persist Directory: %s", settings.CHROMA_PERSIST_DIRECTORY)
    logger.info("Active Gemini Model: %s", settings.GEMINI_MODEL)
    logger.info("CORS Allowed Origins: %s", settings.CORS_ORIGINS)
    yield
    logger.info("Shutting down RAGMate / DocuRAG Backend...")


app = FastAPI(
    title="DocuRAG / RAGMate - Intelligent Document QA API",
    description="FastAPI REST API for Document-Grounded Question Answering using Retrieval-Augmented Generation (RAG)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# PRODUCTION HARDENING MIDDLEWARE (Request-ID, Latency, Security Headers, Rate Limiting)
# =============================================================================

@app.middleware("http")
async def production_hardening_middleware(request: Request, call_next):
    # 1. Request ID tracking
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    request.state.request_id = request_id

    # 2. Rate Limiting on critical endpoints
    path = request.url.path
    if request.method in ("POST", "PUT", "DELETE") and (
        path.startswith("/api/chat")
        or path.startswith("/api/documents/upload")
        or path.startswith("/api/evaluation/run-benchmark")
    ):
        try:
            # 60 requests per minute for resource-heavy generative/upload endpoints
            rate_limiter.check(request, custom_limit=60)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers={"X-Request-ID": request_id, **exc.headers},
            )

    # 3. Request timing & execution
    t0 = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - t0) * 1000
        logger.error(
            "Unhandled exception on %s %s [Request-ID: %s, Duration: %.2f ms]: %s",
            request.method,
            path,
            request_id,
            duration_ms,
            str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error. Please try again later."},
            headers={
                "X-Request-ID": request_id,
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
            },
        )

    duration_ms = (time.perf_counter() - t0) * 1000

    # 4. Attach Security Headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

    # Structured logging (without secrets or payload bodies)
    logger.info(
        "%s %s -> %d (%.2f ms) [ReqID: %s]",
        request.method,
        path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


# Register API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")


# =============================================================================
# SYSTEM & HEALTH ENDPOINTS (Liveness, Readiness, Deep Health)
# =============================================================================

@app.get("/", tags=["System"])
async def root():
    return {
        "project": "DocuRAG / RAGMate",
        "description": "AI-Powered Intelligent Document QA System using RAG",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "status": "operational",
    }


@app.get("/api/health", tags=["System"])
async def health_check():
    """
    Comprehensive system health check inspecting:
    - Relational database connectivity (SQLite / PostgreSQL)
    - Vector database status (ChromaDB persistent collection)
    - Embedding and reranker model configurations
    - Gemini model configuration
    """
    db_status = "healthy"
    vector_status = "healthy"
    details = {}

    # Check Database
    try:
        db = DatabaseManager()
        with db._get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        details["database"] = "connected"
    except Exception as e:
        db_status = "unhealthy"
        details["database"] = f"error: {str(e)}"
        logger.error("Health check database error: %s", e)

    # Check Vector Store
    try:
        vs = VectorStore()
        chunk_count = vs.collection.count()
        details["vector_store"] = f"ready ({chunk_count} indexed chunks)"
    except Exception as e:
        vector_status = "unhealthy"
        details["vector_store"] = f"error: {str(e)}"
        logger.error("Health check vector store error: %s", e)

    overall_status = "ok" if db_status == "healthy" and vector_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "service": "DocuRAG API",
        "version": "1.0.0",
        "database": db_status,
        "vector_store": vector_status,
        "details": details,
        "environment": {
            "embedding_model": settings.EMBEDDING_MODEL,
            "vector_store": "ChromaDB",
            "gemini_model": settings.GEMINI_MODEL,
            "reranker_enabled": settings.RERANKER_ENABLED,
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
        },
    }


@app.get("/api/health/live", tags=["System"])
async def liveness_probe():
    """Kubernetes / Docker container liveness probe."""
    return {"status": "alive", "timestamp": time.time()}


@app.get("/api/health/ready", tags=["System"])
async def readiness_probe():
    """Kubernetes / Docker container readiness probe."""
    try:
        db = DatabaseManager()
        if not db.ping():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is not reachable",
            )
        return {"status": "ready", "database": "connected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Readiness probe check failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies not ready",
        )


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
