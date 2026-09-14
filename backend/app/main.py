"""
DocMind backend application entrypoint.

Wires together configuration, logging, exception handling, CORS, and all
API routers. Run with:

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.routers import ask, documents, health, upload

settings = get_settings()
configure_logging()
logger = get_logger(module="main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: warm up heavy ML models on startup."""
    logger.info("Starting {} v{} ({})", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    try:
        from app.services.embedding import EmbeddingModel
        from app.services.reranker import RerankerModel

        EmbeddingModel.instance()
        RerankerModel.instance()
        logger.info("ML models warmed up successfully.")
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Model warm-up failed at startup; models will lazy-load on first use: {}",
            exc,
        )
    yield
    logger.info("Shutting down {}.", settings.APP_NAME)


def create_app() -> FastAPI:
    """Application factory for DocMind's FastAPI app."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="A private, offline-capable Retrieval-Augmented Generation "
        "system for question answering over uploaded PDF documents.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health.router, prefix=settings.API_V1_PREFIX)
    app.include_router(upload.router, prefix=settings.API_V1_PREFIX)
    app.include_router(ask.router, prefix=settings.API_V1_PREFIX)
    app.include_router(documents.router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
