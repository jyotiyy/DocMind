"""
Custom exception hierarchy for DocMind, plus FastAPI exception handlers that
convert them into structured JSON error responses.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(module="exceptions")


class DocMindError(Exception):
    """Base class for all application-specific errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidFileTypeError(DocMindError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "invalid_file_type"


class FileTooLargeError(DocMindError):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    error_code = "file_too_large"


class PDFParsingError(DocMindError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "pdf_parsing_error"


class OCRProcessingError(DocMindError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "ocr_processing_error"


class EmbeddingGenerationError(DocMindError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "embedding_generation_error"


class VectorStoreError(DocMindError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "vector_store_error"


class DocumentNotFoundError(DocMindError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "document_not_found"


class EmptyIndexError(DocMindError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "empty_index"


class LLMGenerationError(DocMindError):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "llm_generation_error"


class RerankingError(DocMindError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "reranking_error"


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app instance."""

    @app.exception_handler(DocMindError)
    async def docmind_error_handler(request: Request, exc: DocMindError) -> JSONResponse:
        logger.error(
            "Handled application error: {} ({}) at {}",
            exc.message,
            exc.error_code,
            request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception at {}: {}", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
                "details": {},
            },
        )
