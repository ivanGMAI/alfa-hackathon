from http import HTTPStatus

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from database import db_helper
from features.chats.validators import check_chat_permission, get_chat_or_404
from features.documents.export import build_docx, build_pdf, content_disposition
from features.documents.ingest import ingest_pdf, list_chat_documents
from features.documents.schemas import (
    ChatDocumentInfo,
    DocumentExportRequest,
    DocumentUploadResponse,
)
from features.users.models import User
from features.users.service.user import get_current_user_from_cookie

router = APIRouter()

_MEDIA_TYPES = {
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "pdf": "application/pdf",
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/export")
async def export_document(
    payload: DocumentExportRequest,
    user: User = Depends(get_current_user_from_cookie),
):
    """Render text content to a downloadable DOCX or PDF file."""
    if payload.format == "docx":
        data = build_docx(payload.title, payload.content)
    else:
        data = build_pdf(payload.title, payload.content)

    base = (payload.filename or payload.title or "document").strip() or "document"
    return Response(
        content=data,
        media_type=_MEDIA_TYPES[payload.format],
        headers={"Content-Disposition": content_disposition(base, payload.format)},
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=HTTPStatus.CREATED,
)
async def upload_document(
    chat_id: int = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
    user: User = Depends(get_current_user_from_cookie),
):
    """Upload a PDF and index it for retrieval inside the given chat."""
    chat = await get_chat_or_404(session, chat_id)
    check_chat_permission(chat.user_id, user.id)

    filename = (file.filename or "").strip()
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            HTTPStatus.UNPROCESSABLE_ENTITY, "Поддерживаются только PDF-файлы."
        )

    data = await file.read()
    if not data:
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, "Файл пуст.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Файл слишком большой (макс. 10 МБ)."
        )

    try:
        summary = await ingest_pdf(session, chat_id, filename, data)
    except ValueError as exc:
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, str(exc)) from exc

    return DocumentUploadResponse(**summary)


@router.get("", response_model=list[ChatDocumentInfo])
async def list_documents(
    chat_id: int,
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
    user: User = Depends(get_current_user_from_cookie),
):
    """List the documents uploaded to a chat (filename + chunk count)."""
    chat = await get_chat_or_404(session, chat_id)
    check_chat_permission(chat.user_id, user.id)

    rows = await list_chat_documents(session, chat_id)
    return [ChatDocumentInfo(filename=name, chunks=count) for name, count in rows]
