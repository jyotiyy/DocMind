"""Tests for the embedding service (singleton loading, batch/query embedding)."""

from __future__ import annotations

import numpy as np

from app.services.embedding import EmbeddingModel, get_embedding_model


def test_embedding_model_is_singleton() -> None:
    a = get_embedding_model()
    b = get_embedding_model()
    assert a is b
    assert isinstance(a, EmbeddingModel)


def test_embed_texts_returns_normalized_matrix() -> None:
    model = get_embedding_model()
    embeddings = model.embed_texts(["hello world", "DocMind is a RAG system"])
    assert embeddings.shape[0] == 2
    norms = np.linalg.norm(embeddings, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-3)


def test_embed_query_returns_single_vector() -> None:
    model = get_embedding_model()
    vector = model.embed_query("What is DocMind?")
    assert vector.ndim == 1
    assert np.isclose(np.linalg.norm(vector), 1.0, atol=1e-3)


def test_embed_empty_list_returns_empty_array() -> None:
    model = get_embedding_model()
    embeddings = model.embed_texts([])
    assert embeddings.shape[0] == 0
