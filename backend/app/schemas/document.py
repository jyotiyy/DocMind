from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class PageContent(BaseModel):
      page_number: int
    text: str
    used_ocr: bool = False
    char_count: int = 0


class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    section_header: str | None = None
    text: str
    chunk_index: int
    used_ocr: bool = False


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    file_path: str
    file_hash: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    ocr_pages: int
    chunk_ids: list[str] = Field(default_factory=list)
    status: str = "indexed"
    uploaded_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
