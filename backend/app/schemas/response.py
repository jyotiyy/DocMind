from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ConfidenceLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Citation(BaseModel):
 

    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    snippet: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class ConfidenceScore(BaseModel):
  
    score: float = Field(ge=0.0, le=1.0)
    label: ConfidenceLabel
    reason: str


class AskResponse(BaseModel):
  

    answer: str
    citations: list[Citation]
    confidence: ConfidenceScore
    question: str
    documents_searched: int
    retrieved_chunks: int


class UploadedDocumentInfo(BaseModel):
    
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    ocr_pages: int
    status: str


class UploadResponse(BaseModel):
    

    documents: list[UploadedDocumentInfo]
    message: str


class DocumentSummary(BaseModel):
  

    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    ocr_pages: int
    file_size_bytes: int
    uploaded_at: str
    status: str


class DocumentListResponse(BaseModel):
   

    documents: list[DocumentSummary]
    total: int


class DeleteResponse(BaseModel):
   

    document_id: str
    message: str


class ReindexResponse(BaseModel):
   

    reindexed_documents: int
    total_chunks: int
    message: str


class HealthResponse(BaseModel):

    status: str
    version: str
    ollama_reachable: bool
    embedding_model_loaded: bool
    reranker_model_loaded: bool
    total_documents: int
    total_chunks: int
