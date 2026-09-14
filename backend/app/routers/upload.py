"""Router: POST /upload -- upload and ingest one or more PDF documents."""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, status

from app.core.logging import get_logger
from app.dependencies.services import document_manager_dependency
from app.schemas.response import UploadedDocumentInfo, UploadResponse
from app.services.document_manager import DocumentManager
from app.utils.file_utils import generate_document_id, save_upload_file, validate_upload

logger = get_logger(module="upload_router")
router = APIRouter(tags=["upload"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload one or more PDF documents for ingestion",
)
async def upload_documents(
    files: list[UploadFile],
    manager: DocumentManager = Depends(document_manager_dependency),
) -> UploadResponse:
    """Validate, save, parse, chunk, embed, and index each uploaded PDF."""
    uploaded_info: list[UploadedDocumentInfo] = []

    for file in files:
        validate_upload(file)
        document_id = generate_document_id()
        file_path = save_upload_file(file, document_id)

        record = manager.ingest_document(
            document_id=document_id, file_path=file_path, filename=file.filename or "document.pdf"
        )

        uploaded_info.append(
            UploadedDocumentInfo(
                document_id=record.document_id,
                filename=record.filename,
                page_count=record.page_count,
                chunk_count=record.chunk_count,
                ocr_pages=record.ocr_pages,
                status=record.status,
            )
        )

    logger.info("Upload request processed {} file(s).", len(uploaded_info))
    return UploadResponse(
        documents=uploaded_info,
        message=f"Successfully processed {len(uploaded_info)} document(s).",
    )
