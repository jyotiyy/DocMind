"""Router: GET /health -- application and dependency health check."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.config import get_settings
from app.schemas.response import HealthResponse
from app.services.document_manager import get_document_manager
from app.services.embedding import EmbeddingModel
from app.services.llm import check_ollama_health
from app.services.reranker import RerankerModel
from app.services.vector_store import get_vector_store

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check application and dependency health",
)
async def health_check() -> HealthResponse:
    ollama_ok = await check_ollama_health()
    embedding_loaded = EmbeddingModel._instance is not None
    reranker_loaded = RerankerModel._instance is not None

    manager = get_document_manager()
    vector_store = get_vector_store()

    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        ollama_reachable=ollama_ok,
        embedding_model_loaded=embedding_loaded,
        reranker_model_loaded=reranker_loaded,
        total_documents=len(manager.list_documents()),
        total_chunks=vector_store.total_vectors(),
    )
