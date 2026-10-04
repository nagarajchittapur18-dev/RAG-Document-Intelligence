import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"

    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./ragmate.db"

    # Security & Auth Settings
    JWT_SECRET_KEY: str = "ragmate_academic_mca_super_secret_jwt_key_2026_x89q2_production_ready"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_EXPIRATION_MINUTES: int = 1440

    # Vector Store & Embedding Settings
    CHROMA_PERSIST_DIRECTORY: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data")
    )
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # RAG & Ingestion Hyperparameters
    TOP_K: int = 5
    INITIAL_TOP_K: int = 12
    FINAL_TOP_K: int = 5
    MAX_CONTEXT_CHARS: int = 12000
    ENABLE_DOCUMENT_BALANCING: bool = True
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    SIMILARITY_THRESHOLD: float = 0.15
    CHAT_HISTORY_LIMIT: int = 10
    CHAT_MESSAGE_PAGE_SIZE: int = 50

    # Cross-Encoder Reranker Settings
    RERANKER_ENABLED: bool = True
    RERANKING_ENABLED: bool = True
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKING_CANDIDATES: int = 15
    RERANKING_TOP_K: int = 5
    MAX_RERANK_TEXT_LENGTH: int = 1000
    RAG_DEBUG: bool = False

    # File Storage Settings
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 25

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
