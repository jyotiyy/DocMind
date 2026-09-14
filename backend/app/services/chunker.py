from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.document import ChunkMetadata, PageContent
from app.utils.text_utils import extract_last_section_header

logger = get_logger(module="chunker")
settings = get_settings()

_SEPARATORS: list[str] = ["\n\n", "\n", ". ", " ", ""]


class RecursiveCharacterTextSplitter:
   

    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
        separators: list[str] | None = None,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or _SEPARATORS

    def split_text(self, text: str) -> list[str]:
        
        raw_pieces = self._split_recursive(text, self.separators)
        return self._merge_with_overlap(raw_pieces)

    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        if not separators:
            return self._hard_split(text)

        separator, *remaining = separators
        if separator == "":
            return self._hard_split(text)

        parts = text.split(separator)
        pieces: list[str] = []
        for part in parts:
            if not part:
                continue
            if len(part) > self.chunk_size:
                pieces.extend(self._split_recursive(part, remaining))
            else:
                pieces.append(part)
        return pieces

    def _hard_split(self, text: str) -> list[str]:
        return [
            text[i : i + self.chunk_size]
            for i in range(0, len(text), self.chunk_size)
            if text[i : i + self.chunk_size].strip()
        ]

    def _merge_with_overlap(self, pieces: list[str]) -> list[str]:
        
        merged: list[str] = []
        current = ""

        for piece in pieces:
            candidate = f"{current} {piece}".strip() if current else piece
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    merged.append(current)
                current = piece

        if current:
            merged.append(current)

        if self.chunk_overlap == 0 or len(merged) <= 1:
            return merged

        overlapped: list[str] = [merged[0]]
        for i in range(1, len(merged)):
            previous_tail = merged[i - 1][-self.chunk_overlap :]
            overlapped.append(f"{previous_tail} {merged[i]}".strip())
        return overlapped


def chunk_document(
    document_id: str,
    document_name: str,
    pages: list[PageContent],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[ChunkMetadata]:
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.CHUNK_SIZE,
        chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP,
    )

    chunks: list[ChunkMetadata] = []
    running_section_header: str | None = None
    chunk_index = 0

    for page in pages:
        detected_header = extract_last_section_header(page.text)
        if detected_header:
            running_section_header = detected_header

        page_chunks = splitter.split_text(page.text)
        for text in page_chunks:
            if not text.strip():
                continue
            chunks.append(
                ChunkMetadata(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    document_name=document_name,
                    page_number=page.page_number,
                    section_header=running_section_header,
                    text=text.strip(),
                    chunk_index=chunk_index,
                    used_ocr=page.used_ocr,
                )
            )
            chunk_index += 1

    logger.info(
        "Chunked document '{}' into {} chunks across {} pages.",
        document_name,
        len(chunks),
        len(pages),
    )
    return chunks
