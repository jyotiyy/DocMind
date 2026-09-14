from __future__ import annotations

import json
import threading
import zlib
from pathlib import Path

import faiss
import numpy as np

from app.core.config import get_settings
from app.core.exceptions import VectorStoreError
from app.core.logging import get_logger
from app.schemas.document import ChunkMetadata

logger = get_logger(module="vector_store")
settings = get_settings()

_lock = threading.RLock()


def _chunk_id_to_faiss_id(chunk_id: str) -> int:
    
    return zlib.crc32(chunk_id.encode("utf-8")) & 0x7FFFFFFF


class VectorStore:
    
    _instance: "VectorStore | None" = None

    def __init__(self) -> None:
        self.dimension = settings.EMBEDDING_DIMENSION
        self.index_path: Path = settings.FAISS_INDEX_PATH
        self.metadata_path: Path = settings.METADATA_STORE_PATH
        self.index: faiss.Index = self._load_or_create_index()
        self.metadata: dict[int, dict] = self._load_metadata()

    @classmethod
    def instance(cls) -> "VectorStore":
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

   

    def _load_or_create_index(self) -> faiss.Index:
        if self.index_path.exists():
            try:
                logger.info("Loading existing FAISS index from {}", self.index_path)
                return faiss.read_index(str(self.index_path))
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to load existing index ({}); creating a new one.", exc
                )
        return self._create_index()

    def _create_index(self) -> faiss.Index:
        logger.info("Creating new FAISS index (dim={})", self.dimension)
        flat_index = faiss.IndexFlatIP(self.dimension)
        return faiss.IndexIDMap2(flat_index)

    def _load_metadata(self) -> dict[int, dict]:
        if self.metadata_path.exists():
            with self.metadata_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            return {int(k): v for k, v in raw.items()}
        return {}

    def persist(self) -> None:
        """Persist both the FAISS index and metadata store to disk."""
        with _lock:
            faiss.write_index(self.index, str(self.index_path))
            with self.metadata_path.open("w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        logger.info(
            "Persisted vector store ({} vectors) to {}",
            self.index.ntotal,
            self.index_path,
        )

   

    def add_chunks(self, chunks: list[ChunkMetadata], embeddings: np.ndarray) -> None:
        
        if len(chunks) != embeddings.shape[0]:
            raise VectorStoreError(
                "Number of chunks and embeddings must match "
                f"({len(chunks)} vs {embeddings.shape[0]})"
            )
        if embeddings.shape[0] == 0:
            return

        with _lock:
            ids = np.array(
                [_chunk_id_to_faiss_id(c.chunk_id) for c in chunks], dtype=np.int64
            )
            try:
                self.index.add_with_ids(embeddings, ids)
            except Exception as exc:  # noqa: BLE001
                raise VectorStoreError(f"Failed to add vectors to index: {exc}") from exc

            for faiss_id, chunk in zip(ids.tolist(), chunks, strict=True):
                self.metadata[faiss_id] = chunk.model_dump()

            self.persist()
        logger.info("Added {} chunks to vector store.", len(chunks))

    def delete_document(self, document_id: str) -> int:
        
        with _lock:
            ids_to_remove = [
                faiss_id
                for faiss_id, meta in self.metadata.items()
                if meta.get("document_id") == document_id
            ]
            if not ids_to_remove:
                return 0

            id_selector = faiss.IDSelectorArray(np.array(ids_to_remove, dtype=np.int64))
            try:
                self.index.remove_ids(id_selector)
            except Exception as exc:  # noqa: BLE001
                raise VectorStoreError(
                    f"Failed to remove vectors for document {document_id}: {exc}"
                ) from exc

            for faiss_id in ids_to_remove:
                self.metadata.pop(faiss_id, None)

            self.persist()
        logger.info(
            "Deleted {} vectors for document {} from vector store.",
            len(ids_to_remove),
            document_id,
        )
        return len(ids_to_remove)



    def search(
        self,
        query_vector: np.ndarray,
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[tuple[dict, float]]:

        if self.index.ntotal == 0:
            return []

        with _lock:
           
            search_k = top_k if not document_ids else min(self.index.ntotal, top_k * 5)
            scores, ids = self.index.search(
                query_vector.reshape(1, -1).astype(np.float32), search_k
            )

            results: list[tuple[dict, float]] = []
            for score, faiss_id in zip(scores[0], ids[0], strict=True):
                if faiss_id == -1:
                    continue
                meta = self.metadata.get(int(faiss_id))
                if meta is None:
                    continue
                if document_ids and meta.get("document_id") not in document_ids:
                    continue
                results.append((meta, float(score)))
                if len(results) >= top_k:
                    break

        return results

    def total_vectors(self) -> int:
        return self.index.ntotal

    def reset(self) -> None:
        """Wipe the index and metadata entirely (used for full reindex)."""
        with _lock:
            self.index = self._create_index()
            self.metadata = {}
            self.persist()
        logger.warning("Vector store has been fully reset.")


def get_vector_store() -> VectorStore:
    """FastAPI-dependency-friendly accessor for the vector store singleton."""
    return VectorStore.instance()
