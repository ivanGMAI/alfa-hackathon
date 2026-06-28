from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.messages.models import Message
from features.messages.schemas import MessageCreate
from shared.enums import SenderEnum


async def create_message(
    session: AsyncSession,
    message_create: MessageCreate,
    sender: SenderEnum,
) -> Message:
    message = Message(
        **message_create.model_dump(),
        sender=sender,
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def get_messages_for_window(
    session: AsyncSession, chat_id: int, limit: int = 2000
):
    stmt = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    res = await session.execute(stmt)
    return res.scalars().all()
