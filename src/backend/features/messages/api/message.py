from http import HTTPStatus

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

import features.messages.service.message as service
from database import db_helper
from features.messages.schemas import MessageCreate, MessageRead
from features.users.models import User
from features.users.service.user import get_current_user_from_cookie

router = APIRouter()


@router.post(
    "/send",
    response_model=dict[str, MessageRead],
    status_code=HTTPStatus.CREATED,
)
async def send_user_message(
    message_create: MessageCreate,
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
    user: User = Depends(get_current_user_from_cookie),
):
    data = await service.send_message(session, message_create, user.id)
    return data


@router.post("/stream")
async def stream_user_message(
    message_create: MessageCreate,
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
    user: User = Depends(get_current_user_from_cookie),
):
    """Stream the agent's tool steps and answer as Server-Sent Events."""
    generator = service.stream_message(session, message_create, user.id)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
