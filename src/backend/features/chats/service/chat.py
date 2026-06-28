from sqlalchemy.ext.asyncio import AsyncSession

import features.chats.crud.chat as crud
import features.chats.mappers.chat_builder as builder
from features.chats.schemas import ChatCreate, ChatRead, ChatUpdate
from features.chats.validators import check_chat_permission, get_chat_or_404


async def create_chat(
    session: AsyncSession,
    chat_create: ChatCreate,
    user_id: int,
) -> ChatRead:
    chat = await crud.create_chat(session, chat_create, user_id)
    return builder.build_chat_schema(chat, [])


async def get_chat(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
) -> ChatRead:
    chat = await get_chat_or_404(session, chat_id)
    check_chat_permission(chat.user_id, user_id)

    messages = await crud.get_messages_by_chat(session, chat_id)
    return builder.build_chat_schema(chat, messages)


async def update_chat(
    session: AsyncSession,
    chat_id: int,
    chat_update: ChatUpdate,
    user_id: int,
) -> ChatRead:
    chat = await get_chat_or_404(session, chat_id)
    check_chat_permission(chat.user_id, user_id)

    updated = await crud.update_chat(session, chat, chat_update)
    messages = await crud.get_messages_by_chat(session, chat_id)
    return builder.build_chat_schema(updated, messages)


async def delete_chat(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
) -> None:
    chat = await get_chat_or_404(session, chat_id)
    check_chat_permission(chat.user_id, user_id)

    await crud.delete_chat(session, chat)
