"""Tests for the retrieval pipeline: embedding -> FAISS -> rerank."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import EmptyIndexError
from app.services.retriever import build_context, retrieve


def test_retrieve_raises_on_empty_index() -> None:
    with pytest.raises(EmptyIndexError):
        retrieve("What is this document about?")


def test_retrieve_returns_relevant_chunks_after_upload(
    client: TestClient, sample_text_pdf: Path
) -> None:
    with sample_text_pdf.open("rb") as f:
        client.post(
            "/api/v1/upload",
            files=[("files", ("retrieval_test.pdf", f, "application/pdf"))],
        )

    chunks = retrieve("What does DocMind use for vector search?")
    assert len(chunks) > 0
    assert all(chunk.document_name == "retrieval_test.pdf" for chunk in chunks)
    # Chunks should be sorted best-first by rerank score.
    scores = [c.rerank_score for c in chunks]
    assert scores == sorted(scores, reverse=True)


def test_build_context_includes_source_headers(
    client: TestClient, sample_text_pdf: Path
) -> None:
    with sample_text_pdf.open("rb") as f:
        client.post(
            "/api/v1/upload",
            files=[("files", ("context_test.pdf", f, "application/pdf"))],
        )

    chunks = retrieve("What does the architecture section describe?")
    context = build_context(chunks)
    assert "[Source 1" in context
    assert "context_test.pdf" in context
