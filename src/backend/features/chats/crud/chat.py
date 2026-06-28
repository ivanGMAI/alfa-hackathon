from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.chats.models import Chat
from features.chats.schemas import ChatCreate, ChatUpdate
from features.messages.models import Message


async def create_chat(
    session: AsyncSession,
    chat_create: ChatCreate,
    user_id: int,
) -> Chat:
    chat = Chat(**chat_create.model_dump(), user_id=user_id)
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat


async def get_chat_by_id(session: AsyncSession, chat_id: int) -> Chat | None:
    return await session.get(Chat, chat_id)


async def get_messages_by_chat(session: AsyncSession, chat_id: int) -> list[Message]:
    result = await session.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    )
    return list(result.scalars().all())


async def update_chat(
    session: AsyncSession,
    chat: Chat,
    chat_update: ChatUpdate,
) -> Chat:
    update_data = chat_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chat, field, value)
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat


async def delete_chat(session: AsyncSession, chat: Chat) -> None:
    await session.delete(chat)
    await session.commit()
