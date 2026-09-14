"""Tests for GET/DELETE /documents, POST /reindex, and GET /health."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_delete_document_removes_it_from_list(client: TestClient, sample_text_pdf: Path) -> None:
    with sample_text_pdf.open("rb") as f:
        upload_resp = client.post(
            "/api/v1/upload",
            files=[("files", ("to_delete.pdf", f, "application/pdf"))],
        )
    document_id = upload_resp.json()["documents"][0]["document_id"]

    delete_resp = client.delete(f"/api/v1/documents/{document_id}")
    assert delete_resp.status_code == 200

    list_resp = client.get("/api/v1/documents")
    ids = [d["document_id"] for d in list_resp.json()["documents"]]
    assert document_id not in ids


def test_delete_nonexistent_document_returns_404(client: TestClient) -> None:
    response = client.delete("/api/v1/documents/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"] == "document_not_found"


def test_reindex_all_documents(client: TestClient, sample_text_pdf: Path) -> None:
    with sample_text_pdf.open("rb") as f:
        client.post(
            "/api/v1/upload",
            files=[("files", ("reindex_me.pdf", f, "application/pdf"))],
        )

    response = client.post("/api/v1/reindex", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["reindexed_documents"] >= 1
    assert body["total_chunks"] >= 1


def test_health_endpoint_reports_status(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "ollama_reachable" in body
    assert "total_documents" in body
