from http import HTTPStatus

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import features.chats.service.chat as service
from database import db_helper
from features.chats.schemas import ChatCreate, ChatRead, ChatUpdate
from features.users.models import User
from features.users.service.user import get_current_user_from_cookie

router = APIRouter()


@router.post(
    "/",
    response_model=ChatRead,
    status_code=HTTPStatus.CREATED,
)
async def create_chat(
    chat_create: ChatCreate,
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
    user: User = Depends(get_current_user_from_cookie),
):
    data = await service.create_chat(session, chat_create, user.id)
    return data


@router.get(
    "/{chat_id}/",
    response_model=ChatRead,
    status_code=HTTPStatus.OK,
)
async def get_chat(
    chat_id: int,
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
    user: User = Depends(get_current_user_from_cookie),
):
    data = await service.get_chat(session, chat_id, user.id)
    return data


@router.patch(
    "/{chat_id}/",
    response_model=ChatRead,
    status_code=HTTPStatus.OK,
)
async def update_chat(
    chat_id: int,
    chat_update: ChatUpdate,
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
    user: User = Depends(get_current_user_from_cookie),
):
    data = await service.update_chat(session, chat_id, chat_update, user.id)
    return data


@router.delete(
    "/{chat_id}/",
    status_code=HTTPStatus.NO_CONTENT,
)
async def delete_chat(
    chat_id: int,
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
    user: User = Depends(get_current_user_from_cookie),
):
    await service.delete_chat(session, chat_id, user.id)
