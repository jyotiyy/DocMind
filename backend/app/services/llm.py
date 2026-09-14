"""
LLM generation service, backed by a local Ollama instance.

The prompt is deliberately strict: the model is instructed to answer only
from the supplied context and to explicitly say when the context does not
contain the answer, in order to minimize hallucination.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.core.config import get_settings
from app.core.exceptions import LLMGenerationError
from app.core.logging import get_logger

logger = get_logger(module="llm")
settings = get_settings()

SYSTEM_PROMPT = """You are DocMind, a careful document question-answering assistant.

Rules you MUST follow:
1. Answer ONLY using the information contained in the provided context sources.
2. If the context does not contain enough information to answer the question, \
say clearly: "I don't have enough information in the uploaded documents to \
answer this." Do not guess or use outside knowledge.
3. When you state a fact, mention which source number it came from, e.g. (Source 2).
4. Be concise and directly answer the question first, then add supporting detail.
5. Never fabricate page numbers, document names, or facts not present in the context.
"""

USER_PROMPT_TEMPLATE = """Context sources:

{context}

Question: {question}

Answer the question using only the context sources above."""


def _build_messages(question: str, context: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(context=context, question=question),
        },
    ]


async def generate_answer(question: str, context: str) -> str:
    """Generate a complete (non-streaming) grounded answer via Ollama."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": _build_messages(question, context),
        "stream": False,
        "options": {"temperature": settings.OLLAMA_TEMPERATURE},
    }

    url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise LLMGenerationError(f"Failed to reach Ollama at {url}: {exc}") from exc

    message = data.get("message", {})
    content = message.get("content", "").strip()
    if not content:
        raise LLMGenerationError("Ollama returned an empty response.")
    return content


async def stream_answer(question: str, context: str) -> AsyncIterator[str]:
    """Stream a grounded answer from Ollama token-chunk by token-chunk."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": _build_messages(question, context),
        "stream": True,
        "options": {"temperature": settings.OLLAMA_TEMPERATURE},
    }

    url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    import json as _json

                    chunk = _json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break
    except httpx.HTTPError as exc:
        raise LLMGenerationError(f"Failed to stream from Ollama at {url}: {exc}") from exc


async def check_ollama_health() -> bool:
    """Return True if the configured Ollama instance is reachable."""
    url = f"{settings.OLLAMA_BASE_URL}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url)
            return response.status_code == 200
    except httpx.HTTPError:
        return False
