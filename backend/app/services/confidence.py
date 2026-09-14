"""
Confidence scoring service.

Combines FAISS cosine similarity and cross-encoder rerank scores across the
retrieved chunks into a single composite confidence score, label, and
human-readable reason for display in the UI.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.schemas.response import ConfidenceLabel, ConfidenceScore
from app.services.retriever import RetrievedChunk

settings = get_settings()

_RETRIEVAL_WEIGHT = 0.4
_RERANK_WEIGHT = 0.6


def compute_confidence(chunks: list[RetrievedChunk]) -> ConfidenceScore:
    """Compute a composite confidence score from retrieved chunk scores.

    The score blends mean FAISS similarity (recall signal) with mean
    cross-encoder rerank score (precision signal), weighted toward the
    reranker since it is the more accurate relevance estimator.
    """
    if not chunks:
        return ConfidenceScore(
            score=0.0,
            label=ConfidenceLabel.LOW,
            reason="No relevant content was found in the uploaded documents.",
        )

    mean_faiss = sum(c.faiss_score for c in chunks) / len(chunks)
    mean_rerank = sum(c.rerank_score for c in chunks) / len(chunks)

    # FAISS inner-product scores on normalized vectors lie roughly in [-1, 1];
    # clip and rescale to [0, 1] before blending with the rerank score.
    normalized_faiss = max(0.0, min(1.0, (mean_faiss + 1.0) / 2.0))

    composite = (_RETRIEVAL_WEIGHT * normalized_faiss) + (_RERANK_WEIGHT * mean_rerank)
    composite = round(max(0.0, min(1.0, composite)), 4)

    top_score = chunks[0].rerank_score

    if composite >= settings.CONFIDENCE_HIGH_THRESHOLD:
        label = ConfidenceLabel.HIGH
        reason = (
            f"Multiple highly relevant passages were found "
            f"(top match relevance {top_score:.0%}) with strong agreement across sources."
        )
    elif composite >= settings.CONFIDENCE_MEDIUM_THRESHOLD:
        label = ConfidenceLabel.MEDIUM
        reason = (
            f"Relevant passages were found (top match relevance {top_score:.0%}), "
            "but supporting evidence is moderate. Consider verifying against the source."
        )
    else:
        label = ConfidenceLabel.LOW
        reason = (
            f"Only weakly related passages were found (top match relevance {top_score:.0%}). "
            "The answer may be incomplete or the documents may not fully cover this question."
        )

    return ConfidenceScore(score=composite, label=label, reason=reason)
