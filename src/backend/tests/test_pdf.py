"""Tests for PDF text extraction and chunking (no DB, no network)."""

import pytest

from features.documents.export import build_pdf
from features.documents.pdf import MAX_CHUNK_CHARS, chunk_text, extract_pdf_text


def test_chunk_text_empty_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_chunk_text_short_text_is_one_chunk():
    chunks = chunk_text("Короткий договор на одну строку.")
    assert chunks == ["Короткий договор на одну строку."]


def test_chunk_text_packs_paragraphs_within_limit():
    paragraph = "Пункт договора. " * 10  # ~160 chars
    text = "\n\n".join([paragraph] * 12)  # ~1900 chars across 12 paragraphs

    chunks = chunk_text(text, max_chars=400)

    assert len(chunks) > 1
    assert all(len(chunk) <= 400 for chunk in chunks)
    # Every paragraph's text is preserved somewhere.
    assert "Пункт договора." in "".join(chunks)


def test_chunk_text_hard_splits_an_overlong_paragraph():
    paragraph = "А" * (MAX_CHUNK_CHARS * 2 + 50)
    chunks = chunk_text(paragraph)

    assert len(chunks) == 3
    assert all(len(chunk) <= MAX_CHUNK_CHARS for chunk in chunks)
    assert "".join(chunks) == paragraph


def test_extract_pdf_text_round_trip():
    content = "ДОГОВОР оказания услуг\n\nСтороны: ООО «Ромашка» и ИП Иванов.\nСумма: 150 000 ₽"
    pdf_bytes = build_pdf("Договор", content)

    extracted = extract_pdf_text(pdf_bytes)

    assert "ДОГОВОР оказания услуг" in extracted
    assert "Ромашка" in extracted
    assert "150 000" in extracted


def test_extract_pdf_text_rejects_non_pdf_bytes():
    with pytest.raises(ValueError):
        extract_pdf_text(b"this is definitely not a pdf")
