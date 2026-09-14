"""
Citation service.

Converts retrieved chunks into user-facing `Citation` objects, deduplicated
by (document, page) so a document doesn't show 5 citations for the same
page, and with the chunk's relevance score rescaled to [0, 1] for display.
"""

from __future__ import annotations

from app.schemas.response import Citation
from app.services.retriever import RetrievedChunk
from app.utils.text_utils import truncate

_SNIPPET_MAX_CHARS = 280


def build_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    """Build a deduplicated, ranked list of citations from retrieved chunks."""
    seen: set[tuple[str, int]] = set()
    citations: list[Citation] = []

    for chunk in chunks:
        key = (chunk.document_id, chunk.page_number)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            Citation(
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                page_number=chunk.page_number,
                chunk_id=chunk.chunk_id,
                snippet=truncate(chunk.text, _SNIPPET_MAX_CHARS),
                relevance_score=round(max(0.0, min(1.0, chunk.rerank_score)), 4),
            )
        )

    return citations
