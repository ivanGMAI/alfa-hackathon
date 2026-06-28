"""Ingest the markdown knowledge base into pgvector. Run via ``make seed``."""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import delete

from database import db_helper
from features.rag.embeddings import embed_texts
from features.rag.models import KnowledgeChunk

KNOWLEDGE_DIR = Path(__file__).parents[2] / "knowledge"


def chunk_markdown(text: str) -> list[tuple[str, str]]:
    """Split a markdown doc into ``(title, content)`` chunks at ``##`` headings."""
    chunks: list[tuple[str, str]] = []
    title: str | None = None
    lines: list[str] = []

    def flush() -> None:
        if title and lines:
            body = "\n".join(lines).strip()
            if body:
                chunks.append((title, body))

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            title = line[3:].strip()
            lines = [line]
        elif line.startswith("# "):
            continue  # document title — not a chunk boundary
        else:
            lines.append(line)

    flush()
    return chunks


async def ingest() -> int:
    files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    records: list[tuple[str, str, str]] = []
    for file in files:
        for title, content in chunk_markdown(file.read_text(encoding="utf-8")):
            records.append((file.stem, title, content))

    if not records:
        print(f"No knowledge found in {KNOWLEDGE_DIR}")
        return 0

    embeddings = await embed_texts([content for _, _, content in records])

    async with db_helper.session_factory() as session:
        await session.execute(delete(KnowledgeChunk))  # full refresh on every run
        for (source, title, content), embedding in zip(records, embeddings):
            session.add(
                KnowledgeChunk(
                    source=source, title=title, content=content, embedding=embedding
                )
            )
        await session.commit()

    await db_helper.dispose()
    print(f"Ingested {len(records)} chunks from {len(files)} files.")
    return len(records)


if __name__ == "__main__":
    asyncio.run(ingest())
