import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ragmate")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing RAGMate Intelligent Document QA Backend...")
    logger.info("Active Embedding Model: %s", settings.EMBEDDING_MODEL)
    logger.info("ChromaDB Persist Directory: %s", settings.CHROMA_PERSIST_DIRECTORY)
    logger.info("CORS Allowed Origins: %s", settings.CORS_ORIGINS)
    yield
    logger.info("Shutting down RAGMate Backend...")


app = FastAPI(
    title="RAGMate - Intelligent Document QA API",
    description="FastAPI Backend for AI-Powered Document Question Answering using Retrieval-Augmented Generation (RAG)",
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


@app.get("/", tags=["System"])
async def root():
    return {
        "project": "RAGMate",
        "description": "AI-Powered Intelligent Document QA System using RAG",
        "version": "1.0.0",
        "docs_url": "/docs",
        "status": "operational",
    }


@app.get("/api/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": {
            "embedding_model": settings.EMBEDDING_MODEL,
            "vector_store": "ChromaDB",
            "database": "SQLite (aiosqlite) / PostgreSQL ready",
            "reranker_enabled": settings.RERANKER_ENABLED,
            "gemini_model": settings.GEMINI_MODEL,
        },
    }
