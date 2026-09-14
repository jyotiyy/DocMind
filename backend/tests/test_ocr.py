"""Tests for the OCR service and scanned-page detection in the PDF parser."""

from __future__ import annotations

from pathlib import Path

from app.services.ocr import page_requires_ocr
from app.services.pdf_parser import parse_pdf


def test_page_requires_ocr_detects_sparse_text() -> None:
    assert page_requires_ocr("", min_chars=20) is True
    assert page_requires_ocr("a b", min_chars=20) is True


def test_page_requires_ocr_allows_sufficient_text() -> None:
    long_text = "This page contains a reasonable amount of selectable text content."
    assert page_requires_ocr(long_text, min_chars=20) is False


def test_text_pdf_does_not_trigger_ocr(sample_text_pdf: Path) -> None:
    parsed = parse_pdf(sample_text_pdf, "sample_text.pdf")
    assert parsed.ocr_pages == 0
    assert all(not page.used_ocr for page in parsed.pages)


def test_scanned_pdf_triggers_ocr_pathway(sample_scanned_pdf: Path) -> None:
    """A blank/scanned page should be routed through OCR (text may be empty)."""
    parsed = parse_pdf(sample_scanned_pdf, "sample_scanned.pdf")
    assert parsed.ocr_pages == 1
    assert parsed.pages[0].used_ocr is True
