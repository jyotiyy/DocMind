"""
FastAPI dependency-injection accessors.

Routers depend on these thin functions rather than importing service
singletons directly, which keeps routers testable via `app.dependency_overrides`.
"""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.services.document_manager import DocumentManager, get_document_manager
from app.services.embedding import EmbeddingModel, get_embedding_model
from app.services.reranker import RerankerModel, get_reranker_model
from app.services.vector_store import VectorStore, get_vector_store


def settings_dependency() -> Settings:
    return get_settings()


def document_manager_dependency() -> DocumentManager:
    return get_document_manager()


def vector_store_dependency() -> VectorStore:
    return get_vector_store()


def embedding_model_dependency() -> EmbeddingModel:
    return get_embedding_model()


def reranker_model_dependency() -> RerankerModel:
    return get_reranker_model()
