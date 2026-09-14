

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.logging import get_logger
from app.dependencies.services import document_manager_dependency
from app.schemas.request import ReindexRequest
from app.schemas.response import (
    DeleteResponse,
    DocumentListResponse,
    DocumentSummary,
    ReindexResponse,
)
from app.services.document_manager import DocumentManager

logger = get_logger(module="documents_router")
router = APIRouter(tags=["documents"])


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all indexed documents",
)
async def list_documents(
    manager: DocumentManager = Depends(document_manager_dependency),
) -> DocumentListResponse:
    records = manager.list_documents()
    summaries = [
        DocumentSummary(
            document_id=r.document_id,
            filename=r.filename,
            page_count=r.page_count,
            chunk_count=r.chunk_count,
            ocr_pages=r.ocr_pages,
            file_size_bytes=r.file_size_bytes,
            uploaded_at=r.uploaded_at,
            status=r.status,
        )
        for r in records
    ]
    return DocumentListResponse(documents=summaries, total=len(summaries))


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a document and rebuild the index",
)
async def delete_document(
    document_id: str,
    manager: DocumentManager = Depends(document_manager_dependency),
) -> DeleteResponse:
    manager.delete_document(document_id)
    logger.info("Deleted document {} via API request.", document_id)
    return DeleteResponse(
        document_id=document_id, message="Document deleted and index updated."
    )


@router.post(
    "/reindex",
    response_model=ReindexResponse,
    status_code=status.HTTP_200_OK,
    summary="Rebuild the vector index for one, several, or all documents",
)
async def reindex_documents(
    request: ReindexRequest,
    manager: DocumentManager = Depends(document_manager_dependency),
) -> ReindexResponse:
    reindexed_count, total_chunks = manager.reindex(request.document_ids)
    return ReindexResponse(
        reindexed_documents=reindexed_count,
        total_chunks=total_chunks,
        message=f"Reindexed {reindexed_count} document(s).",
    )
