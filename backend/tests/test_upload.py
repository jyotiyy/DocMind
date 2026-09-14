"""Tests for POST /upload and the document ingestion pipeline."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_upload_text_pdf_success(client: TestClient, sample_text_pdf: Path) -> None:
    with sample_text_pdf.open("rb") as f:
        response = client.post(
            "/api/v1/upload",
            files=[("files", ("sample_text.pdf", f, "application/pdf"))],
        )

    assert response.status_code == 201
    body = response.json()
    assert len(body["documents"]) == 1
    doc = body["documents"][0]
    assert doc["filename"] == "sample_text.pdf"
    assert doc["page_count"] == 1
    assert doc["chunk_count"] >= 1
    assert doc["ocr_pages"] == 0
    assert doc["status"] == "indexed"


def test_upload_rejects_non_pdf(client: TestClient, tmp_path: Path) -> None:
    bad_file = tmp_path / "not_a_pdf.txt"
    bad_file.write_text("hello world")

    with bad_file.open("rb") as f:
        response = client.post(
            "/api/v1/upload",
            files=[("files", ("not_a_pdf.txt", f, "text/plain"))],
        )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_file_type"


def test_upload_multiple_files(client: TestClient, sample_text_pdf: Path) -> None:
    with sample_text_pdf.open("rb") as f1, sample_text_pdf.open("rb") as f2:
        response = client.post(
            "/api/v1/upload",
            files=[
                ("files", ("doc1.pdf", f1, "application/pdf")),
                ("files", ("doc2.pdf", f2, "application/pdf")),
            ],
        )

    assert response.status_code == 201
    assert len(response.json()["documents"]) == 2


def test_uploaded_document_appears_in_list(client: TestClient, sample_text_pdf: Path) -> None:
    with sample_text_pdf.open("rb") as f:
        client.post(
            "/api/v1/upload",
            files=[("files", ("listed.pdf", f, "application/pdf"))],
        )

    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    filenames = [d["filename"] for d in response.json()["documents"]]
    assert "listed.pdf" in filenames
