from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):

    question: str = Field(
        ..., min_length=3, max_length=2000, description="The user's natural-language question."
    )
    document_ids: list[str] | None = Field(
        default=None,
        description="Optional subset of document IDs to restrict retrieval to. "
        "If omitted, all indexed documents are searched.",
    )
    top_k: int | None = Field(
        default=None, ge=1, le=20, description="Override the number of chunks retrieved."
    )
    stream: bool = Field(default=False, description="Whether to stream the answer via SSE.")

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


class ReindexRequest(BaseModel):

    document_ids: list[str] | None = Field(
        default=None,
        description="Specific document IDs to rebuild. If omitted, rebuilds the entire index.",
    )
