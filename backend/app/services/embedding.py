"""
Embedding service.

Wraps a SentenceTransformer model (`all-MiniLM-L6-v2`) as a process-wide
singleton to avoid reloading weights on every request. Provides batch
embedding for document chunks and single-vector embedding for queries,
with L2 normalization so that inner-product search in FAISS is equivalent
to cosine similarity.
"""

from __future__ import annotations

import threading

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.exceptions import EmbeddingGenerationError
from app.core.logging import get_logger

logger = get_logger(module="embedding")
settings = get_settings()

_lock = threading.Lock()


class EmbeddingModel:
    """Thread-safe singleton wrapper around a SentenceTransformer model."""

    _instance: "EmbeddingModel | None" = None

    def __init__(self) -> None:
        logger.info("Loading embedding model '{}'...", settings.EMBEDDING_MODEL_NAME)
        try:
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingGenerationError(
                f"Failed to load embedding model: {exc}"
            ) from exc
        logger.info("Embedding model loaded successfully.")

    @classmethod
    def instance(cls) -> "EmbeddingModel":
        """Return the process-wide singleton, creating it on first use."""
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def is_loaded(self) -> bool:
        return self._model is not None

    def embed_texts(self, texts: list[str], batch_size: int | None = None) -> np.ndarray:
        """Embed a batch of texts, returning an (N, D) L2-normalized float32 array."""
        if not texts:
            return np.zeros((0, settings.EMBEDDING_DIMENSION), dtype=np.float32)
        try:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size or settings.EMBEDDING_BATCH_SIZE,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingGenerationError(f"Failed to embed texts: {exc}") from exc
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string, returning a (D,) L2-normalized float32 vector."""
        return self.embed_texts([query])[0]


def get_embedding_model() -> EmbeddingModel:
    """FastAPI-dependency-friendly accessor for the embedding model singleton."""
    return EmbeddingModel.instance()
