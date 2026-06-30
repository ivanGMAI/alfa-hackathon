"""Extract text from PDF bytes and split it into RAG-sized chunks.

``chunk_text`` is pure (no I/O) so it is unit-tested directly. ``extract_pdf_text``
wraps ``pypdf`` and is exercised by the live upload flow.
"""

from __future__ import annotations

import io
import re

MAX_CHUNK_CHARS = 900


def extract_pdf_text(data: bytes) -> str:
    """Return the concatenated text of every page of a PDF.

    Raises ``ValueError`` if the bytes are not a readable PDF.
    """
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except (PdfReadError, OSError, ValueError) as exc:
        raise ValueError(f"Не удалось прочитать PDF: {exc}") from exc

    return "\n\n".join(pages).strip()


def pdf_page_count(data: bytes) -> int:
    from pypdf import PdfReader

    return len(PdfReader(io.BytesIO(data)).pages)


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text into paragraph-aligned chunks of at most ~``max_chars``.

    Paragraphs are packed together up to the limit; a single paragraph longer
    than the limit is hard-split. Returns an empty list for blank input.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buffer = ""

    def flush() -> None:
        nonlocal buffer
        if buffer:
            chunks.append(buffer)
            buffer = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            flush()
            for start in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[start : start + max_chars])
            continue
        if buffer and len(buffer) + len(paragraph) + 1 > max_chars:
            flush()
        buffer = f"{buffer}\n{paragraph}" if buffer else paragraph

    flush()
    return chunks
