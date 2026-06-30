"""Vector similarity search over the knowledge base (pgvector cosine distance)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.rag.embeddings import embed_query
from features.rag.models import ChatDocumentChunk, KnowledgeChunk


@dataclass
class RetrievedChunk:
    title: str
    source: str
    content: str


async def search_knowledge(
    session: AsyncSession,
    query: str,
    k: int = 3,
) -> list[RetrievedChunk]:
    """Return the ``k`` most relevant knowledge chunks for ``query``.

    Returns an empty list if the query is blank or the knowledge base is empty,
    so callers can treat RAG as an optional augmentation.
    """
    if not query.strip():
        return []

    query_vector = await embed_query(query)
    stmt = (
        select(KnowledgeChunk)
        .order_by(KnowledgeChunk.embedding.cosine_distance(query_vector))
        .limit(k)
    )
    result = await session.execute(stmt)
    return [
        RetrievedChunk(title=row.title, source=row.source, content=row.content)
        for row in result.scalars().all()
    ]


async def search_chat_documents(
    session: AsyncSession,
    chat_id: int,
    query: str,
    k: int = 4,
) -> list[RetrievedChunk]:
    """Return the ``k`` most relevant chunks of documents uploaded to ``chat_id``.

    Empty when the query is blank or the chat has no uploaded documents, so the
    caller can treat per-chat document grounding as an optional augmentation.
    """
    if not query.strip():
        return []

    query_vector = await embed_query(query)
    stmt = (
        select(ChatDocumentChunk)
        .where(ChatDocumentChunk.chat_id == chat_id)
        .order_by(ChatDocumentChunk.embedding.cosine_distance(query_vector))
        .limit(k)
    )
    result = await session.execute(stmt)
    return [
        RetrievedChunk(title=row.filename, source=row.filename, content=row.content)
        for row in result.scalars().all()
    ]
