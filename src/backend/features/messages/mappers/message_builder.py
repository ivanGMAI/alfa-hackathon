from features.messages.models import Message
from features.messages.schemas import MessageRead


def build_message_schema(message: Message) -> MessageRead:
    return MessageRead.model_validate(message)
