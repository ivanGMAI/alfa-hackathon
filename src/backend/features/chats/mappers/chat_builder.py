from features.chats.models import Chat
from features.chats.schemas import ChatRead
from features.messages.models import Message
from features.messages.schemas import MessageRead


def build_chat_schema(chat: Chat, messages: list[Message]) -> ChatRead:
    return ChatRead(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at,
        messages=(
            [MessageRead.model_validate(m) for m in messages] if messages != [] else []
        ),
    )
