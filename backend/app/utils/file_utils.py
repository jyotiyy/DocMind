"""File-system and upload-related utility functions."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError
from app.core.logging import get_logger

logger = get_logger(module="file_utils")
settings = get_settings()


def validate_upload(file: UploadFile) -> None:
    """Validate a single uploaded file's extension against the allow-list.

    Size validation happens while streaming to disk in `save_upload_file`,
    since UploadFile does not reliably expose size ahead of time.
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(
            f"File type '{suffix}' is not supported. Allowed types: "
            f"{', '.join(sorted(settings.ALLOWED_EXTENSIONS))}"
        )


def generate_document_id() -> str:
    """Generate a unique document identifier."""
    return str(uuid.uuid4())


def save_upload_file(file: UploadFile, document_id: str) -> Path:
    """Stream an uploaded file to disk under the upload directory.

    Raises:
        FileTooLargeError: if the file exceeds the configured max size.
    """
    destination = settings.UPLOAD_DIR / f"{document_id}.pdf"
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    written = 0

    with destination.open("wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                buffer.close()
                destination.unlink(missing_ok=True)
                raise FileTooLargeError(
                    f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
                )
            buffer.write(chunk)

    file.file.seek(0)
    logger.info("Saved upload '{}' -> {} ({} bytes)", file.filename, destination, written)
    return destination


def compute_file_hash(path: Path) -> str:
    """Compute a SHA-256 hash of a file's contents for de-duplication."""
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def delete_file(path: Path) -> None:
    """Delete a file from disk if it exists."""
    if path.exists():
        path.unlink()
        logger.info("Deleted file {}", path)


def remove_directory(path: Path) -> None:
    """Recursively remove a directory if it exists."""
    if path.exists():
        shutil.rmtree(path)
        logger.info("Removed directory {}", path)
