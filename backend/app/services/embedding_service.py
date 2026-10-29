import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings

logger = logging.getLogger("ragmate.embedding_service")


class EmbeddingService:
    """
    Cached, thread-safe service for generating dense vector embeddings using SentenceTransformers.
    Uses singleton model loading to prevent repetitive disk I/O and GPU/CPU memory overhead.
    """

    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None
    _model_name: Optional[str] = None

    def __new__(cls, model_name: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialize_model(model_name or settings.EMBEDDING_MODEL)
        elif model_name and cls._instance._model_name != model_name:
            cls._instance._initialize_model(model_name)
        return cls._instance

    def _initialize_model(self, model_name: str) -> None:
        """Loads and caches the SentenceTransformer embedding model."""
        logger.info("Initializing SentenceTransformer embedding model: %s", model_name)
        self._model_name = model_name
        try:
            self._model = SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            self._model = SentenceTransformer(model_name)
        if hasattr(self._model, "get_embedding_dimension"):
            self.embedding_dimension = self._model.get_embedding_dimension()
        else:
            self.embedding_dimension = self._model.get_sentence_embedding_dimension()
        logger.info(
            "Embedding model '%s' loaded successfully (dimension: %d)",
            model_name,
            self.embedding_dimension,
        )

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._initialize_model(settings.EMBEDDING_MODEL)
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """Generates a normalized dense embedding vector for a single text string."""
        if not text or not text.strip():
            # Return zero vector if text is empty
            return [0.0] * self.embedding_dimension

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding.tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Embeds a user search query.
        Applies L2 normalization for accurate cosine similarity matching.
        """
        return self.embed_text(query.strip())

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generates normalized dense embeddings for a batch of text strings."""
        if not texts:
            return []

        clean_texts = [t.strip() if t and t.strip() else " " for t in texts]

        embeddings = self.model.encode(
            clean_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()
