"""
Retrieval pipeline.

Orchestrates: question -> query embedding -> FAISS top-K -> cross-encoder
rerank -> top-N context assembly. This is the single entry point the `ask`
router uses to fetch grounding context for the LLM.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.exceptions import EmptyIndexError
from app.core.logging import get_logger
from app.services.embedding import get_embedding_model
from app.services.reranker import rerank
from app.services.vector_store import get_vector_store

logger = get_logger(module="retriever")
settings = get_settings()


@dataclass
class RetrievedChunk:
    """A single chunk retrieved and scored for a query."""

    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    section_header: str | None
    text: str
    faiss_score: float
    rerank_score: float


def retrieve(
    question: str,
    document_ids: list[str] | None = None,
    retrieval_top_k: int | None = None,
    rerank_top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Run the full retrieval pipeline for a natural-language question.

    Args:
        question: The user's question.
        document_ids: Optional subset of document IDs to restrict search to.
        retrieval_top_k: Override for the initial FAISS candidate count.
        rerank_top_k: Override for the final reranked result count.

    Returns:
        A list of RetrievedChunk, best-first, of length <= rerank_top_k.

    Raises:
        EmptyIndexError: if the vector store has no indexed content.
    """
    store = get_vector_store()
    if store.total_vectors() == 0:
        raise EmptyIndexError(
            "No documents have been indexed yet. Upload a PDF before asking questions."
        )

    embedding_model = get_embedding_model()
    query_vector = embedding_model.embed_query(question)

    k1 = retrieval_top_k or settings.RETRIEVAL_TOP_K
    k2 = rerank_top_k or settings.RERANK_TOP_K

    candidates = store.search(query_vector, top_k=k1, document_ids=document_ids)
    logger.info("FAISS returned {} candidates for question.", len(candidates))

    if not candidates:
        return []

    reranked = rerank(question, candidates, top_k=k2)

    results = [
        RetrievedChunk(
            chunk_id=meta["chunk_id"],
            document_id=meta["document_id"],
            document_name=meta["document_name"],
            page_number=meta["page_number"],
            section_header=meta.get("section_header"),
            text=meta["text"],
            faiss_score=faiss_score,
            rerank_score=rerank_score,
        )
        for meta, faiss_score, rerank_score in reranked
    ]
    logger.info("Reranked down to {} chunks for context.", len(results))
    return results


def build_context(chunks: list[RetrievedChunk]) -> str:
    """Assemble retrieved chunks into a single formatted context block for the LLM."""
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        header = f"[Source {i} | Document: {chunk.document_name} | Page: {chunk.page_number}"
        if chunk.section_header:
            header += f" | Section: {chunk.section_header}"
        header += "]"
        blocks.append(f"{header}\n{chunk.text}")
    return "\n\n---\n\n".join(blocks)
