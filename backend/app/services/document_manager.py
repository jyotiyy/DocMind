"""
Document manager service.

Owns the document registry (persisted JSON list of DocumentRecord) and
orchestrates the full ingestion pipeline: parse -> chunk -> embed -> store.
Also handles deletion and full/partial reindexing.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import DocumentNotFoundError
from app.core.logging import get_logger
from app.schemas.document import DocumentRecord
from app.services.chunker import chunk_document
from app.services.embedding import get_embedding_model
from app.services.pdf_parser import parse_pdf
from app.services.vector_store import get_vector_store
from app.utils.file_utils import compute_file_hash, delete_file

logger = get_logger(module="document_manager")
settings = get_settings()

_lock = threading.RLock()


class DocumentManager:
    """Singleton managing the document registry and ingestion pipeline."""

    _instance: "DocumentManager | None" = None

    def __init__(self) -> None:
        self.registry_path: Path = settings.DOCUMENT_REGISTRY_PATH
        self.records: dict[str, DocumentRecord] = self._load_registry()

    @classmethod
    def instance(cls) -> "DocumentManager":
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    # Registry persistence
    # ------------------------------------------------------------------ #

    def _load_registry(self) -> dict[str, DocumentRecord]:
        if self.registry_path.exists():
            with self.registry_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            return {doc_id: DocumentRecord(**data) for doc_id, data in raw.items()}
        return {}

    def _persist_registry(self) -> None:
        with self.registry_path.open("w", encoding="utf-8") as f:
            json.dump(
                {doc_id: record.model_dump() for doc_id, record in self.records.items()},
                f,
                ensure_ascii=False,
                indent=2,
            )

    # ------------------------------------------------------------------ #
    # Ingestion
    # ------------------------------------------------------------------ #

    def ingest_document(self, document_id: str, file_path: Path, filename: str) -> DocumentRecord:
        """Run the full ingestion pipeline for one uploaded PDF.

        Parses the PDF (with OCR fallback), chunks the text, embeds every
        chunk, stores the vectors, and registers the document.
        """
        parsed = parse_pdf(file_path, filename)
        chunks = chunk_document(
            document_id=document_id,
            document_name=filename,
            pages=parsed.pages,
        )

        embedding_model = get_embedding_model()
        vector_store = get_vector_store()

        if chunks:
            texts = [c.text for c in chunks]
            embeddings = embedding_model.embed_texts(texts)
            vector_store.add_chunks(chunks, embeddings)

        record = DocumentRecord(
            document_id=document_id,
            filename=filename,
            file_path=str(file_path),
            file_hash=compute_file_hash(file_path),
            file_size_bytes=file_path.stat().st_size,
            page_count=parsed.page_count,
            chunk_count=len(chunks),
            ocr_pages=parsed.ocr_pages,
            chunk_ids=[c.chunk_id for c in chunks],
            status="indexed",
        )

        with _lock:
            self.records[document_id] = record
            self._persist_registry()

        logger.info(
            "Ingested document '{}' ({}): {} pages, {} chunks, {} OCR pages.",
            filename,
            document_id,
            record.page_count,
            record.chunk_count,
            record.ocr_pages,
        )
        return record

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_documents(self) -> list[DocumentRecord]:
        return sorted(
            self.records.values(), key=lambda r: r.uploaded_at, reverse=True
        )

    def get_document(self, document_id: str) -> DocumentRecord:
        record = self.records.get(document_id)
        if record is None:
            raise DocumentNotFoundError(f"Document '{document_id}' was not found.")
        return record

    def total_chunks(self) -> int:
        return sum(record.chunk_count for record in self.records.values())

    # ------------------------------------------------------------------ #
    # Deletion & reindexing
    # ------------------------------------------------------------------ #

    def delete_document(self, document_id: str) -> None:
        """Remove a document's file, vectors, and registry entry."""
        record = self.get_document(document_id)
        vector_store = get_vector_store()

        with _lock:
            vector_store.delete_document(document_id)
            delete_file(Path(record.file_path))
            self.records.pop(document_id, None)
            self._persist_registry()

        logger.info("Deleted document '{}' ({}).", record.filename, document_id)

    def reindex(self, document_ids: list[str] | None = None) -> tuple[int, int]:
        """Rebuild vectors for the given documents (or all documents).

        Returns:
            (number_of_documents_reindexed, total_chunks_after_reindex)
        """
        targets = (
            [self.get_document(doc_id) for doc_id in document_ids]
            if document_ids
            else list(self.records.values())
        )

        vector_store = get_vector_store()
        reindexed_count = 0

        with _lock:
            for record in targets:
                vector_store.delete_document(record.document_id)
                file_path = Path(record.file_path)
                if not file_path.exists():
                    logger.warning(
                        "Skipping reindex for '{}': source file missing.", record.filename
                    )
                    continue
                new_record = self.ingest_document(
                    record.document_id, file_path, record.filename
                )
                self.records[record.document_id] = new_record
                reindexed_count += 1

            self._persist_registry()

        return reindexed_count, self.total_chunks()


def get_document_manager() -> DocumentManager:
    """FastAPI-dependency-friendly accessor for the document manager singleton."""
    return DocumentManager.instance()
