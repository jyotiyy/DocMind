"""Shared pytest fixtures for the DocMind backend test suite."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


@pytest.fixture(scope="session", autouse=True)
def _isolated_data_dirs(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Redirect all persistent storage paths to a temp directory for the test run."""
    settings = get_settings()
    test_root = tmp_path_factory.mktemp("docmind_test_data")

    settings.DATA_DIR = test_root / "data"
    settings.UPLOAD_DIR = test_root / "data" / "uploads"
    settings.INDEX_DIR = test_root / "indexes"
    settings.FAISS_INDEX_PATH = settings.INDEX_DIR / "faiss.index"
    settings.METADATA_STORE_PATH = settings.INDEX_DIR / "metadata.json"
    settings.DOCUMENT_REGISTRY_PATH = settings.INDEX_DIR / "documents.json"
    settings.LOG_DIR = test_root / "logs"
    settings.ensure_directories()

    yield

    shutil.rmtree(test_root, ignore_errors=True)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A FastAPI TestClient with the app's lifespan events triggered."""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_text_pdf(tmp_path: Path) -> Path:
    """Create a simple PDF with real selectable text (no OCR needed)."""
    pdf_path = tmp_path / "sample_text.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Introduction\n\n"
        "DocMind is a retrieval-augmented question answering system. "
        "It allows users to upload PDF documents and ask natural language "
        "questions grounded strictly in the uploaded content.\n\n"
        "Architecture\n\n"
        "The system uses FAISS for vector search and a cross-encoder for "
        "reranking retrieved passages before generation.",
        fontsize=11,
    )
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def sample_scanned_pdf(tmp_path: Path) -> Path:
    """Create a PDF with no selectable text at all, simulating a scanned page."""
    pdf_path = tmp_path / "sample_scanned.pdf"
    doc = fitz.open()
    doc.new_page()  # blank page, no text layer
    doc.save(pdf_path)
    doc.close()
    return pdf_path
