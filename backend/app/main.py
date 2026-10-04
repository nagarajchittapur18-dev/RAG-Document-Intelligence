import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.evaluation import router as evaluation_router
from app.config import settings

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

# Register API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")


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
    return {
        "status": "ok",
        "service": "DocuRAG API",
        "version": "1.0.0",
        "environment": {
            "embedding_model": settings.EMBEDDING_MODEL,
            "vector_store": "ChromaDB",
            "gemini_model": settings.GEMINI_MODEL,
            "reranker_enabled": settings.RERANKER_ENABLED,
        },
    }
