"""Tests for POST /ask, with Ollama mocked out so no live LLM is required."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _mock_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch the LLM service so tests never hit a real Ollama server."""

    async def fake_generate_answer(question: str, context: str) -> str:
        return (
            "DocMind uses FAISS for vector search and a cross-encoder for "
            "reranking retrieved passages (Source 1)."
        )

    monkeypatch.setattr(
        "app.routers.ask.generate_answer", AsyncMock(side_effect=fake_generate_answer)
    )


def _upload(client: TestClient, pdf_path: Path, filename: str) -> None:
    with pdf_path.open("rb") as f:
        response = client.post(
            "/api/v1/upload",
            files=[("files", (filename, f, "application/pdf"))],
        )
    assert response.status_code == 201


def test_ask_without_any_documents_returns_no_info_answer(client: TestClient) -> None:
    response = client.post("/api/v1/ask", json={"question": "What is in the documents?"})
    assert response.status_code == 200
    body = response.json()
    assert "don't have enough information" in body["answer"]
    assert body["confidence"]["label"] == "low"
    assert body["citations"] == []


def test_ask_with_indexed_document_returns_grounded_answer(
    client: TestClient, sample_text_pdf: Path
) -> None:
    _upload(client, sample_text_pdf, "ask_test.pdf")

    response = client.post(
        "/api/v1/ask",
        json={"question": "What does DocMind use for vector search?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "FAISS" in body["answer"]
    assert len(body["citations"]) > 0
    assert body["citations"][0]["document_name"] == "ask_test.pdf"
    assert body["confidence"]["score"] >= 0.0
    assert body["retrieved_chunks"] > 0


def test_ask_rejects_blank_question(client: TestClient) -> None:
    response = client.post("/api/v1/ask", json={"question": "  "})
    assert response.status_code == 422


def test_ask_can_filter_by_document_id(client: TestClient, sample_text_pdf: Path) -> None:
    _upload(client, sample_text_pdf, "filtered_doc.pdf")
    docs_response = client.get("/api/v1/documents")
    document_id = docs_response.json()["documents"][0]["document_id"]

    response = client.post(
        "/api/v1/ask",
        json={
            "question": "What does the document describe?",
            "document_ids": [document_id],
        },
    )
    assert response.status_code == 200
    for citation in response.json()["citations"]:
        assert citation["document_id"] == document_id
