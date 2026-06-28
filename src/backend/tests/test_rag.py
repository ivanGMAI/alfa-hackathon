"""Tests for RAG: local embeddings, markdown chunking, knowledge injection."""

import math

import pytest

from features.llm.context_builder import build_messages
from features.rag.embeddings import embed_texts, local_embed
from features.rag.ingest import chunk_markdown
from features.rag.models import EMBEDDING_DIM


class FakeMessage:
    def __init__(self, sender: str, content: str):
        self.sender = sender
        self.content = content


def test_local_embed_shape_and_normalization():
    vector = local_embed("маржа и наценка для бизнеса")
    assert len(vector) == EMBEDDING_DIM
    norm = math.sqrt(sum(value * value for value in vector))
    assert abs(norm - 1.0) < 1e-6


def test_local_embed_is_deterministic():
    assert local_embed("одно и то же") == local_embed("одно и то же")


def test_local_embed_distinguishes_topics():
    assert local_embed("налоги усн патент") != local_embed("маркетинг реклама воронка")


@pytest.mark.asyncio
async def test_embed_texts_empty_and_local():
    assert await embed_texts([]) == []
    vectors = await embed_texts(["первый", "второй"])
    assert len(vectors) == 2
    assert all(len(v) == EMBEDDING_DIM for v in vectors)


def test_chunk_markdown_splits_on_h2_and_skips_title():
    markdown = (
        "# Заголовок документа\n\n"
        "## Раздел A\nсодержимое A\n\n"
        "## Раздел B\nсодержимое B\n"
    )
    chunks = dict(chunk_markdown(markdown))
    assert list(chunks.keys()) == ["Раздел A", "Раздел B"]
    assert "содержимое A" in chunks["Раздел A"]


def test_build_messages_injects_knowledge_as_system():
    messages = build_messages(
        [FakeMessage("user", "вопрос")],
        knowledge=["Маржа — это доля прибыли в выручке"],
    )
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    assert "базы знаний" in messages[1]["content"]
    assert "[1]" in messages[1]["content"]
    assert messages[2] == {"role": "user", "content": "вопрос"}


def test_build_messages_without_knowledge_has_single_system():
    messages = build_messages([FakeMessage("user", "вопрос")])
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
