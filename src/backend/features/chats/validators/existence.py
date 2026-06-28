from sqlalchemy.ext.asyncio import AsyncSession

import features.chats.crud.chat as crud
from features.chats.exceptions import ChatNotFoundException
from features.chats.models import Chat


async def get_chat_or_404(
    session: AsyncSession,
    chat_id: int,
) -> Chat:
    chat = await crud.get_chat_by_id(session, chat_id)
    if not chat:
        raise ChatNotFoundException()
    return chat
