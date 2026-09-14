"""
Cross-encoder reranking service.

FAISS retrieval (bi-encoder) is fast but approximate; a cross-encoder that
jointly attends over (query, passage) pairs gives a much more accurate
relevance ranking. We use it to rerank the top-K FAISS candidates down to a
smaller, higher-precision set before answer generation.
"""

from __future__ import annotations

import threading

from sentence_transformers import CrossEncoder

from app.core.config import get_settings
from app.core.exceptions import RerankingError
from app.core.logging import get_logger

logger = get_logger(module="reranker")
settings = get_settings()

_lock = threading.Lock()


class RerankerModel:
    """Thread-safe singleton wrapper around a CrossEncoder model."""

    _instance: "RerankerModel | None" = None

    def __init__(self) -> None:
        logger.info("Loading reranker model '{}'...", settings.RERANKER_MODEL_NAME)
        try:
            self._model = CrossEncoder(settings.RERANKER_MODEL_NAME)
        except Exception as exc:  # noqa: BLE001
            raise RerankingError(f"Failed to load reranker model: {exc}") from exc
        logger.info("Reranker model loaded successfully.")

    @classmethod
    def instance(cls) -> "RerankerModel":
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def is_loaded(self) -> bool:
        return self._model is not None

    def score(self, query: str, passages: list[str]) -> list[float]:
        """Score each (query, passage) pair, returning raw relevance scores."""
        if not passages:
            return []
        try:
            pairs = [(query, passage) for passage in passages]
            scores = self._model.predict(pairs, show_progress_bar=False)
        except Exception as exc:  # noqa: BLE001
            raise RerankingError(f"Cross-encoder scoring failed: {exc}") from exc
        return [float(s) for s in scores]


def get_reranker_model() -> RerankerModel:
    """FastAPI-dependency-friendly accessor for the reranker singleton."""
    return RerankerModel.instance()


def _sigmoid(x: float) -> float:
    import math

    return 1.0 / (1.0 + math.exp(-x))


def rerank(
    query: str, candidates: list[tuple[dict, float]], top_k: int
) -> list[tuple[dict, float, float]]:
    """Rerank FAISS candidates using the cross-encoder.

    Args:
        query: The user's question.
        candidates: List of (chunk_metadata, faiss_similarity) tuples.
        top_k: Number of top reranked results to keep.

    Returns:
        List of (chunk_metadata, faiss_similarity, rerank_score) tuples,
        sorted by rerank_score descending, where rerank_score is a
        sigmoid-normalized value in [0, 1].
    """
    if not candidates:
        return []

    model = get_reranker_model()
    passages = [meta["text"] for meta, _ in candidates]
    raw_scores = model.score(query, passages)
    normalized_scores = [_sigmoid(s) for s in raw_scores]

    combined = [
        (meta, faiss_score, rerank_score)
        for (meta, faiss_score), rerank_score in zip(
            candidates, normalized_scores, strict=True
        )
    ]
    combined.sort(key=lambda item: item[2], reverse=True)
    return combined[:top_k]
