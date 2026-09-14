"""
OCR service for scanned / image-only PDF pages.

Workflow for a page lacking selectable text:
  1. Render the page at a high DPI (default 300) to a raster image.
  2. Convert to grayscale.
  3. Apply binary thresholding to increase contrast.
  4. Apply a light denoising filter.
  5. Run pytesseract to extract text.
"""

from __future__ import annotations

import io

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageFilter

from app.core.config import get_settings
from app.core.exceptions import OCRProcessingError
from app.core.logging import get_logger
from app.utils.text_utils import clean_text

logger = get_logger(module="ocr")
settings = get_settings()

_BINARIZATION_THRESHOLD = 180


def _render_page_to_image(doc: "fitz.Document", page_index: int, dpi: int) -> Image.Image:
    """Render a PDF page to a PIL Image at the given DPI."""
    page = doc.load_page(page_index)
    zoom = dpi / 72.0  # PDF base resolution is 72 DPI
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
    return image


def _preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Apply grayscale conversion, thresholding, and denoising to an image."""
    grayscale = image.convert("L")
    denoised = grayscale.filter(ImageFilter.MedianFilter(size=3))
    thresholded = denoised.point(
        lambda pixel: 255 if pixel > _BINARIZATION_THRESHOLD else 0
    )
    return thresholded


def ocr_page(doc: "fitz.Document", page_index: int) -> str:
    """Run the full OCR pipeline on a single page and return cleaned text.

    Args:
        doc: An open PyMuPDF document.
        page_index: Zero-based index of the page to OCR.

    Returns:
        Cleaned OCR text for the page (may be empty if OCR finds nothing).

    Raises:
        OCRProcessingError: if rendering or OCR extraction fails.
    """
    try:
        image = _render_page_to_image(doc, page_index, settings.OCR_DPI)
        preprocessed = _preprocess_for_ocr(image)
        raw_text = pytesseract.image_to_string(
            preprocessed, lang=settings.OCR_LANGUAGE
        )
        text = clean_text(raw_text)
        logger.debug(
            "OCR extracted {} chars from page {}", len(text), page_index + 1
        )
        return text
    except Exception as exc:  # noqa: BLE001
        raise OCRProcessingError(
            f"OCR failed on page {page_index + 1}: {exc}"
        ) from exc


def page_requires_ocr(text: str, min_chars: int) -> bool:
    """Return True if the given extracted text is too sparse to be reliable."""
    return len(text.strip()) < min_chars
