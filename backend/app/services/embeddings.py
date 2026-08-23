"""Embedding provider abstraction.

Three backends behind one interface:

- **hashing** (default, offline, zero heavy deps): deterministic signed
  feature-hashing of tokens into a fixed-dim unit vector. Good enough for local
  dev, tests, and demos without any model download or API key.
- **openai**: OpenAI embeddings (used when OPENAI_API_KEY is set). Requires the
  `ai` extra (`pip install -e ".[ai]"`).
- **local**: sentence-transformers model. Requires the `local-embeddings` extra
  (pulls PyTorch).

`get_embedder()` chooses based on settings.llm_provider ("auto" picks openai when
a key exists, else hashing). Every embedder exposes `.dim`, which must equal
settings.embedding_dim so stored vectors match the DB column width.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, runtime_checkable

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@runtime_checkable
class Embedder(Protocol):
    name: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic, dependency-free embedder via signed feature hashing."""

    name = "hashing"

    def __init__(self, dim: int) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            for token in _TOKEN_RE.findall(text.lower()):
                digest = int(hashlib.md5(token.encode()).hexdigest(), 16)
                idx = digest % self.dim
                sign = 1.0 if (digest >> 1) & 1 == 0 else -1.0
                vec[idx] += sign
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vectors.append([v / norm for v in vec])
        return vectors


class OpenAIEmbedder:
    name = "openai"

    def __init__(self, dim: int, api_key: str, model: str = "text-embedding-3-small") -> None:
        self.dim = dim
        self.model = model
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("openai not installed; run: pip install -e '.[ai]'") from exc
        self._client = OpenAI(api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(
            model=self.model, input=texts, dimensions=self.dim
        )
        return [item.embedding for item in resp.data]


class SentenceTransformerEmbedder:
    name = "local"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "sentence-transformers not installed; run: pip install -e '.[local-embeddings]'"
            ) from exc
        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vec.tolist() for vec in self._model.encode(texts, normalize_embeddings=True)]


def get_embedder() -> Embedder:
    provider = settings.llm_provider
    if provider == "auto":
        provider = "openai" if settings.openai_api_key else "hashing"

    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set")
        return OpenAIEmbedder(dim=settings.embedding_dim, api_key=settings.openai_api_key)
    if provider == "local":
        embedder = SentenceTransformerEmbedder()
        if embedder.dim != settings.embedding_dim:
            logger.warning(
                "local embedder dim %s != EMBEDDING_DIM %s; set EMBEDDING_DIM to match",
                embedder.dim,
                settings.embedding_dim,
            )
        return embedder
    return HashingEmbedder(dim=settings.embedding_dim)
