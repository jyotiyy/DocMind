"""Pydantic response models for the DocMind API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ConfidenceLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Citation(BaseModel):
    """A single page-level citation backing an answer."""

    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    snippet: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class ConfidenceScore(BaseModel):
    """Composite confidence assessment for a generated answer."""

    score: float = Field(ge=0.0, le=1.0)
    label: ConfidenceLabel
    reason: str


class AskResponse(BaseModel):
    """Response body for POST /ask (non-streaming)."""

    answer: str
    citations: list[Citation]
    confidence: ConfidenceScore
    question: str
    documents_searched: int
    retrieved_chunks: int


class UploadedDocumentInfo(BaseModel):
    """Summary information returned immediately after a successful upload."""

    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    ocr_pages: int
    status: str


class UploadResponse(BaseModel):
    """Response body for POST /upload."""

    documents: list[UploadedDocumentInfo]
    message: str


class DocumentSummary(BaseModel):
    """A document entry as returned by GET /documents."""

    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    ocr_pages: int
    file_size_bytes: int
    uploaded_at: str
    status: str


class DocumentListResponse(BaseModel):
    """Response body for GET /documents."""

    documents: list[DocumentSummary]
    total: int


class DeleteResponse(BaseModel):
    """Response body for DELETE /documents/{id}."""

    document_id: str
    message: str


class ReindexResponse(BaseModel):
    """Response body for POST /reindex."""

    reindexed_documents: int
    total_chunks: int
    message: str


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str
    version: str
    ollama_reachable: bool
    embedding_model_loaded: bool
    reranker_model_loaded: bool
    total_documents: int
    total_chunks: int
