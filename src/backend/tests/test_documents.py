"""Tests for the DOCX / PDF document export builders."""

import io
import zipfile

from features.documents.export import build_docx, build_pdf, content_disposition

CONTENT = "СЧЁТ на оплату\nОт: ООО «Ромашка»\nИтого: 12 500 ₽"


def test_build_docx_is_a_valid_zip_with_content():
    data = build_docx("Счёт №1", CONTENT)

    assert zipfile.is_zipfile(io.BytesIO(data))
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = set(archive.namelist())
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "word/document.xml" in names
        document = archive.read("word/document.xml").decode("utf-8")

    # Title and every content line land in the document body (Cyrillic preserved).
    assert "Счёт №1" in document
    assert "ООО «Ромашка»" in document
    assert "Итого: 12 500 ₽" in document


def test_build_docx_escapes_xml_special_characters():
    data = build_docx(None, "Цена < 100 & скидка > 0")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")

    assert "&lt;" in document and "&amp;" in document and "&gt;" in document
    assert "< 100 & скидка >" not in document  # raw specials must not leak


def test_build_pdf_returns_a_pdf_document():
    data = build_pdf("Договор", CONTENT)

    assert data.startswith(b"%PDF-")
    assert data.rstrip().endswith(b"%%EOF")
    assert len(data) > 1000  # a real page, not an empty stub


def test_build_pdf_handles_blank_lines_without_error():
    # Blank lines exercise the ``pdf.ln`` branch.
    data = build_pdf(None, "Первая строка\n\n\nПоследняя строка")
    assert data.startswith(b"%PDF-")


def test_content_disposition_has_ascii_fallback_and_utf8_name():
    header = content_disposition("Счёт", "docx")

    assert header.startswith("attachment;")
    assert 'filename="' in header  # ASCII fallback present
    assert "filename*=UTF-8''" in header
    assert "%D0" in header  # percent-encoded Cyrillic
