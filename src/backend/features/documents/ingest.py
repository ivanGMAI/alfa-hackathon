"""Ingest an uploaded PDF into per-chat RAG storage (parse → chunk → embed → store)."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from features.documents.pdf import chunk_text, extract_pdf_text, pdf_page_count
from features.rag.embeddings import embed_texts
from features.rag.models import ChatDocumentChunk


async def ingest_pdf(
    session: AsyncSession,
    chat_id: int,
    filename: str,
    data: bytes,
) -> dict:
    """Parse a PDF, chunk + embed it, and store the chunks for ``chat_id``.

    Re-uploading the same filename replaces its previous chunks. Raises
    ``ValueError`` when the PDF has no extractable text (e.g. a scan).
    """
    pages = pdf_page_count(data)
    text = extract_pdf_text(data)
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError(
            "В PDF не найден текстовый слой — возможно, это скан без распознанного текста."
        )

    embeddings = await embed_texts(chunks)

    # Replace any earlier upload of the same file in this chat to avoid duplicates.
    await session.execute(
        delete(ChatDocumentChunk).where(
            ChatDocumentChunk.chat_id == chat_id,
            ChatDocumentChunk.filename == filename,
        )
    )
    for chunk, embedding in zip(chunks, embeddings):
        session.add(
            ChatDocumentChunk(
                chat_id=chat_id,
                filename=filename,
                title=filename,
                content=chunk,
                embedding=embedding,
            )
        )
    await session.commit()

    return {"filename": filename, "pages": pages, "chunks": len(chunks)}


async def list_chat_documents(
    session: AsyncSession, chat_id: int
) -> list[tuple[str, int]]:
    """Return ``(filename, chunk_count)`` for each document uploaded to ``chat_id``."""
    stmt = (
        select(ChatDocumentChunk.filename, func.count())
        .where(ChatDocumentChunk.chat_id == chat_id)
        .group_by(ChatDocumentChunk.filename)
        .order_by(ChatDocumentChunk.filename)
    )
    result = await session.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]
