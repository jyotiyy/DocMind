"""Tests for the RecursiveCharacterTextSplitter and chunk_document pipeline."""

from __future__ import annotations

from app.schemas.document import PageContent
from app.services.chunker import RecursiveCharacterTextSplitter, chunk_document


def test_splitter_respects_chunk_size() -> None:
    splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
    text = "word " * 100  # 500 chars
    chunks = splitter.split_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 60 for c in chunks)  # allow overlap slack


def test_splitter_short_text_returns_single_chunk() -> None:
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    text = "This is a short piece of text."
    chunks = splitter.split_text(text)
    assert chunks == [text]


def test_splitter_rejects_invalid_overlap() -> None:
    try:
        RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=100)
        assert False, "Expected ValueError for overlap >= chunk_size"
    except ValueError:
        pass


def test_chunk_document_preserves_page_and_section_metadata() -> None:
    pages = [
        PageContent(
            page_number=1,
            text="Overview\n\nThis document describes the system architecture in detail "
            "across multiple paragraphs of explanatory text that should be chunked.",
            used_ocr=False,
            char_count=140,
        ),
        PageContent(
            page_number=2,
            text="Results\n\nThe evaluation shows strong retrieval accuracy on the test set.",
            used_ocr=False,
            char_count=80,
        ),
    ]

    chunks = chunk_document(
        document_id="doc-1",
        document_name="test.pdf",
        pages=pages,
        chunk_size=60,
        chunk_overlap=10,
    )

    assert len(chunks) > 0
    assert all(c.document_id == "doc-1" for c in chunks)
    page_numbers = {c.page_number for c in chunks}
    assert page_numbers == {1, 2}
    assert any(c.section_header == "Overview" for c in chunks)
    assert any(c.section_header == "Results" for c in chunks)
