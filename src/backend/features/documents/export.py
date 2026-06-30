"""Render plain-text business documents to downloadable DOCX / PDF bytes.

Both builders are pure functions (text in, bytes out) so they are trivially
unit-testable and have no side effects. DOCX is hand-rolled with the stdlib
``zipfile`` (a .docx is just a zip of XML), which keeps it dependency-free and
naturally UTF-8 / Cyrillic safe. PDF uses ``fpdf2`` with a vendored Unicode
font (DejaVu Sans) so Cyrillic renders correctly — the stock PDF base-14 fonts
do not carry Cyrillic glyphs.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

FONT_PATH = Path(__file__).parent / "fonts" / "DejaVuSans.ttf"

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.'
    'wordprocessingml.document.main+xml"/>'
    "</Types>"
)

_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
    'officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)


def _paragraph(text: str, *, bold: bool = False, size: int | None = None) -> str:
    props = ""
    if bold:
        props += "<w:b/>"
    if size:
        props += f'<w:sz w:val="{size * 2}"/>'  # OOXML sizes are in half-points
    rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
    return (
        f"<w:p>{('<w:pPr>' + rpr + '</w:pPr>') if rpr else ''}"
        f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'
    )


def build_docx(title: str | None, content: str) -> bytes:
    """Build a minimal but valid .docx, one paragraph per line of ``content``."""
    paragraphs = []
    if title:
        paragraphs.append(_paragraph(title, bold=True, size=16))
    for line in content.split("\n"):
        paragraphs.append(_paragraph(line))

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/'
        'wordprocessingml/2006/main"><w:body>'
        + "".join(paragraphs)
        + "<w:sectPr/></w:body></w:document>"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
        archive.writestr("_rels/.rels", _RELS)
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def build_pdf(title: str | None, content: str) -> bytes:
    """Build a PDF with the vendored Unicode font so Cyrillic renders correctly."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    # Return the cursor to the left margin and the next line after each block, so
    # consecutive multi_cell calls always have the full page width to work with.
    flow = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("DejaVu", "", str(FONT_PATH))
    pdf.set_font("DejaVu", size=11)

    if title:
        pdf.set_font_size(15)
        pdf.multi_cell(0, 9, title, **flow)
        pdf.ln(2)
        pdf.set_font_size(11)

    for line in content.split("\n"):
        if line.strip():
            pdf.multi_cell(0, 6, line, **flow)
        else:
            pdf.ln(4)

    return bytes(pdf.output())


def content_disposition(base: str, fmt: str) -> str:
    """Build a Content-Disposition header that survives non-ASCII (Cyrillic) names.

    Provides an ASCII fallback plus an RFC 5987 ``filename*`` with the real name.
    """
    name = f"{base}.{fmt}"
    ascii_base = base.encode("ascii", "ignore").decode().strip()
    ascii_fallback = f"{ascii_base}.{fmt}" if ascii_base else f"document.{fmt}"
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(name)}"
