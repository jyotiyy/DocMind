"""
PDF parsing service.

Responsible for opening a PDF, extracting selectable text page-by-page,
detecting pages that require OCR (scanned/image-only pages), and delegating
those pages to the OCR service. Also extracts document-level metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from app.core.config import get_settings
from app.core.exceptions import PDFParsingError
from app.core.logging import get_logger
from app.schemas.document import PageContent
from app.services.ocr import ocr_page
from app.utils.text_utils import clean_text

logger = get_logger(module="pdf_parser")
settings = get_settings()


@dataclass
class ParsedDocument:
    """Result of parsing a PDF: metadata plus per-page content."""

    filename: str
    page_count: int
    pages: list[PageContent]
    ocr_pages: int
    title: str | None
    author: str | None


def _extract_metadata(doc: "fitz.Document") -> dict[str, str | None]:
    """Pull document-level metadata (title/author) from the PDF, if present."""
    meta = doc.metadata or {}
    return {
        "title": meta.get("title") or None,
        "author": meta.get("author") or None,
    }


def parse_pdf(file_path: Path, filename: str) -> ParsedDocument:
    """Parse a PDF file into per-page text content, applying OCR as needed.

    Args:
        file_path: Path to the PDF on disk.
        filename: Original filename, used for logging/metadata only.

    Returns:
        A ParsedDocument containing extracted page content.

    Raises:
        PDFParsingError: if the file cannot be opened or parsed.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as exc:  # noqa: BLE001 - PyMuPDF raises generic exceptions
        raise PDFParsingError(f"Failed to open PDF '{filename}': {exc}") from exc

    if doc.page_count == 0:
        doc.close()
        raise PDFParsingError(f"PDF '{filename}' contains no pages.")

    metadata = _extract_metadata(doc)
    pages: list[PageContent] = []
    ocr_page_count = 0

    try:
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            raw_text = page.get_text("text") or ""
            cleaned = clean_text(raw_text)

            if len(cleaned) >= settings.MIN_TEXT_CHARS_PER_PAGE:
                pages.append(
                    PageContent(
                        page_number=page_index + 1,
                        text=cleaned,
                        used_ocr=False,
                        char_count=len(cleaned),
                    )
                )
                continue

            logger.info(
                "Page {} of '{}' has insufficient selectable text ({} chars); "
                "routing to OCR.",
                page_index + 1,
                filename,
                len(cleaned),
            )
            ocr_text = ocr_page(doc, page_index)
            ocr_page_count += 1
            pages.append(
                PageContent(
                    page_number=page_index + 1,
                    text=ocr_text,
                    used_ocr=True,
                    char_count=len(ocr_text),
                )
            )
    finally:
        doc.close()

    logger.info(
        "Parsed '{}': {} pages, {} required OCR.",
        filename,
        len(pages),
        ocr_page_count,
    )

    return ParsedDocument(
        filename=filename,
        page_count=len(pages),
        pages=pages,
        ocr_pages=ocr_page_count,
        title=metadata["title"],
        author=metadata["author"],
    )
