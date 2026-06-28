"""Text embeddings for RAG.

Two backends, chosen by ``settings.llm.embedding_mode``:

* ``"local"`` (default) — a deterministic, dependency-free hashed bag-of-words
  embedding. No API needed, so ingestion and retrieval run offline and in tests.
* ``"api"`` — an OpenAI-compatible ``/embeddings`` endpoint (production quality).

Both produce ``EMBEDDING_DIM``-length L2-normalized vectors so the same pgvector
column works regardless of backend.
"""

from __future__ import annotations

import hashlib
import math
import re

from core.config import settings
from features.rag.models import EMBEDDING_DIM

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _hashed_features(token: str) -> list[str]:
    # The word itself plus its character trigrams, for some fuzzy matching.
    trigrams = [token[i : i + 3] for i in range(max(1, len(token) - 2))]
    return [token, *trigrams]


def local_embed(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIM
    for token in _TOKEN_RE.findall(text.lower()):
        for feature in _hashed_features(token):
            digest = int(hashlib.md5(feature.encode("utf-8")).hexdigest(), 16)
            index = digest % EMBEDDING_DIM
            sign = 1.0 if (digest >> 1) & 1 else -1.0
            vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


async def _api_embed(texts: list[str]) -> list[list[float]]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.llm.api_key,
        base_url=settings.llm.api_base,
        timeout=settings.llm.request_timeout,
    )
    response = await client.embeddings.create(
        model=settings.llm.embedding_model, input=texts
    )
    return [item.embedding for item in response.data]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.llm.embedding_mode == "api":
        return await _api_embed(texts)
    return [local_embed(text) for text in texts]


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]
