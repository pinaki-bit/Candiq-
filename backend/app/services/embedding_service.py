"""
backend/app/services/embedding_service.py

Abstract Embedding Service Layer.

Provides provider-agnostic vector embeddings and semantic similarity computations.

Supported Providers:
  - LocalEmbeddingProvider (Default TF-IDF / L2 normalized feature vector fallback)
  - OpenAIEmbeddingProvider (OpenAI text-embedding-3-small via httpx API)
  - BGEEmbeddingProvider (Local SentenceTransformer BGE model adapter)

API Interface:
  - embed_text(text: str) -> list[float]
  - embed_document(text: str) -> list[float]
  - embed_batch(texts: list[str]) -> list[list[float]]
  - similarity(vec1: list[float], vec2: list[float]) -> float
"""

from __future__ import annotations

import abc
import math
import logging
from functools import lru_cache
from typing import List

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vector lists. Returns value in [0.0, 1.0]."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    
    sim = dot / (norm_a * norm_b)
    # Clamp to [0, 1]
    return max(0.0, min(1.0, float(sim)))


class BaseEmbeddingProvider(abc.ABC):
    """Abstract interface for vector embedding providers."""

    @abc.abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a short text query."""
        pass

    @abc.abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of texts."""
        pass


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic Local Feature Vector Embedding Fallback.
    Uses TF-IDF feature vocabulary projection + Hashing vectorizer to 128-dim dense embedding.
    Does not require external API keys or heavy GPU downloads.
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dim

        # Deterministic hashing vectorizer projection
        import hashlib
        words = [w.strip().lower() for w in text.split() if len(w.strip()) > 1]
        vec = [0.0] * self.dim
        if not words:
            return vec

        for word in words:
            # Hash to index
            idx = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[idx] += 1.0

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [round(v / norm, 6) for v in vec]
        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI API Embedding Provider (`text-embedding-3-small`)."""
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.fallback = LocalEmbeddingProvider()

    def embed_text(self, text: str) -> List[float]:
        if not self.api_key:
            logger.warning("OpenAI API key missing; falling back to LocalEmbeddingProvider.")
            return self.fallback.embed_text(text)

        import httpx
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"input": text, "model": self.model},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
        except Exception as exc:
            logger.error("OpenAI embedding request failed (%s); using fallback.", exc)
            return self.fallback.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            return self.fallback.embed_batch(texts)

        import httpx
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"input": texts, "model": self.model},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
        except Exception as exc:
            logger.error("OpenAI batch embedding failed (%s); using fallback.", exc)
            return self.fallback.embed_batch(texts)


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """
    Production Local SentenceTransformer Semantic Vector Provider.
    Uses sentence-transformers/all-MiniLM-L6-v2 (384-dim normalized dense vector).
    Falls back gracefully to LocalEmbeddingProvider if package or model is unavailable.
    """
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.device = device
        self._model = None
        self.dim = 384
        self.fallback = LocalEmbeddingProvider()
        self._failed = False

    def _ensure_loaded(self):
        if self._model is None and not self._failed:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(
                    "Initializing SentenceTransformer model '%s' on %s...",
                    self.model_name, self.device
                )
                self._model = SentenceTransformer(self.model_name, device=self.device)
                logger.info(
                    "SentenceTransformer model '%s' initialized successfully.", self.model_name
                )
            except Exception as exc:
                logger.warning(
                    "Failed to load SentenceTransformer model '%s' (%s); activating LocalEmbeddingProvider fallback.",
                    self.model_name, exc
                )
                self._failed = True

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dim

        self._ensure_loaded()
        if self._failed or self._model is None:
            return self.fallback.embed_text(text)

        try:
            vec = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return [float(x) for x in vec]
        except Exception as exc:
            logger.error("SentenceTransformer embed_text failed (%s); using fallback.", exc)
            return self.fallback.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        self._ensure_loaded()
        if self._failed or self._model is None:
            return self.fallback.embed_batch(texts)

        try:
            vecs = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=32)
            return [[float(x) for x in row] for row in vecs]
        except Exception as exc:
            logger.error("SentenceTransformer embed_batch failed (%s); using fallback.", exc)
            return self.fallback.embed_batch(texts)


class EmbeddingService:
    """Main abstracted Embedding & Semantic Similarity Service."""

    def __init__(self, provider: BaseEmbeddingProvider | None = None):
        if provider is None:
            from app.config import get_settings
            settings = get_settings()
            provider_type = settings.embedding_provider.lower().strip()
            if provider_type in ("sentence_transformer", "sentence_transformers", "minilm", "bge"):
                self.provider = SentenceTransformerEmbeddingProvider(
                    model_name=settings.sentence_transformer_model,
                    device=settings.embedding_device,
                )
            elif provider_type == "openai":
                self.provider = OpenAIEmbeddingProvider(
                    api_key=settings.openai_api_key,
                    model=settings.openai_embedding_model,
                )
            elif provider_type == "local":
                self.provider = LocalEmbeddingProvider()
            else:
                self.provider = SentenceTransformerEmbeddingProvider(
                    model_name=settings.sentence_transformer_model,
                    device=settings.embedding_device,
                )
        else:
            self.provider = provider

    def embed_text(self, text: str) -> List[float]:
        """Return vector embedding for a query or title."""
        return self.provider.embed_text(text)

    def embed_document(self, doc_text: str) -> List[float]:
        """Return vector embedding for a multi-paragraph resume or job description."""
        # Truncate very long documents to avoid API token overflow
        truncated = doc_text[:4000] if doc_text else ""
        return self.provider.embed_text(truncated)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Return vector embeddings for a list of documents."""
        return self.provider.embed_batch(texts)

    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute normalized cosine similarity in range [0.0, 1.0]."""
        return cosine_similarity(vec1, vec2)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Return singleton instance of EmbeddingService."""
    return EmbeddingService()

