

from __future__ import annotations

import json

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.schemas.request import AskRequest
from app.schemas.response import AskResponse
from app.services.citation import build_citations
from app.services.confidence import compute_confidence
from app.services.llm import generate_answer, stream_answer
from app.services.retriever import build_context, retrieve

logger = get_logger(module="ask_router")
router = APIRouter(tags=["ask"])


@router.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question grounded in the uploaded documents",
)
async def ask_question(request: AskRequest):
   
    chunks = retrieve(
        question=request.question,
        document_ids=request.document_ids,
        retrieval_top_k=request.top_k,
    )
    context = build_context(chunks)
    citations = build_citations(chunks)
    confidence = compute_confidence(chunks)

    if not request.stream:
        if chunks:
            answer = await generate_answer(request.question, context)
        else:
            answer = (
                "I don't have enough information in the uploaded documents to "
                "answer this."
            )
        logger.info(
            "Answered question (non-streaming). chunks={} confidence={}",
            len(chunks),
            confidence.label,
        )
        return AskResponse(
            answer=answer,
            citations=citations,
            confidence=confidence,
            question=request.question,
            documents_searched=len({c.document_id for c in chunks}),
            retrieved_chunks=len(chunks),
        )

    async def event_generator():
        if chunks:
            async for token in stream_answer(request.question, context):
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        else:
            fallback = (
                "I don't have enough information in the uploaded documents to "
                "answer this."
            )
            yield f"event: token\ndata: {json.dumps({'token': fallback})}\n\n"

        final_payload = {
            "citations": [c.model_dump() for c in citations],
            "confidence": confidence.model_dump(),
            "documents_searched": len({c.document_id for c in chunks}),
            "retrieved_chunks": len(chunks),
        }
        yield f"event: done\ndata: {json.dumps(final_payload)}\n\n"

    logger.info("Answering question (streaming). chunks={}", len(chunks))
    return StreamingResponse(event_generator(), media_type="text/event-stream")
