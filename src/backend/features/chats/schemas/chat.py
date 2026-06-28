from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from features.messages.schemas import MessageRead


class ChatBase(BaseModel):
    title: str | None = None


class ChatCreate(ChatBase):
    pass


class ChatUpdate(ChatBase):
    pass


class ChatRead(ChatBase):
    id: int
    created_at: datetime
    messages: List[MessageRead] = []

    model_config = ConfigDict(from_attributes=True)
