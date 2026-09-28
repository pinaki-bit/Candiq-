"""
backend/tests/test_embedding_service.py

Unit tests for the EmbeddingService layer.
Tests SentenceTransformer embedding provider, local vector embeddings, cosine similarity computation, batch embedding, and provider fallback.
"""

from __future__ import annotations

import pytest
from app.services.embedding_service import (
    EmbeddingService,
    LocalEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    cosine_similarity,
    get_embedding_service,
)


class TestEmbeddingService:
    def test_local_provider_returns_vector(self):
        provider = LocalEmbeddingProvider(dim=64)
        vec = provider.embed_text("Machine learning engineer with Python and TensorFlow")
        assert len(vec) == 64
        assert isinstance(vec[0], float)
        assert sum(vec) > 0.0

    def test_similarity_identical_vectors(self):
        vec = [0.5, 0.5, 0.5, 0.5]
        sim = cosine_similarity(vec, vec)
        assert round(sim, 4) == 1.0

    def test_similarity_orthogonal_vectors(self):
        v1 = [1.0, 0.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0, 0.0]
        sim = cosine_similarity(v1, v2)
        assert sim == 0.0

    def test_embedding_service_document_and_similarity(self):
        service = EmbeddingService(provider=LocalEmbeddingProvider(dim=128))
        v1 = service.embed_document("Python FastAPI software engineer")
        v2 = service.embed_document("Backend Python web developer with FastAPI")
        sim = service.similarity(v1, v2)
        assert 0.0 <= sim <= 1.0
        assert sim > 0.1  # should have positive semantic similarity

    def test_batch_embeddings(self):
        service = EmbeddingService(provider=LocalEmbeddingProvider(dim=32))
        texts = ["Data Science", "Web Development", "DevOps Cloud"]
        batch_vecs = service.embed_batch(texts)
        assert len(batch_vecs) == 3
        for vec in batch_vecs:
            assert len(vec) == 32

    def test_sentence_transformer_provider_returns_384_dim_normalized_vector(self):
        provider = SentenceTransformerEmbeddingProvider()
        vec = provider.embed_text("Senior Python Backend Engineer specializing in microservices and FastAPI.")
        assert len(vec) == 384
        assert isinstance(vec[0], float)
        # Verify L2 norm ~ 1.0
        norm = sum(x * x for x in vec) ** 0.5
        assert round(norm, 3) == 1.0

    def test_sentence_transformer_batch_embeddings(self):
        provider = SentenceTransformerEmbeddingProvider()
        texts = [
            "Python backend developer",
            "Data Science ML engineer",
            "Cybersecurity analyst",
        ]
        batch = provider.embed_batch(texts)
        assert len(batch) == 3
        for vec in batch:
            assert len(vec) == 384

    def test_sentence_transformer_fallback_on_invalid_model(self):
        """Verify graceful fallback to LocalEmbeddingProvider on loading error."""
        provider = SentenceTransformerEmbeddingProvider(model_name="invalid/nonexistent-model-xyz-123")
        vec = provider.embed_text("Testing fallback behavior")
        assert len(vec) == 128  # Fallback LocalEmbeddingProvider dim
        assert provider._failed is True

    def test_get_embedding_service_singleton_resolution(self):
        service = get_embedding_service()
        assert isinstance(service.provider, SentenceTransformerEmbeddingProvider)
