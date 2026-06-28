from datetime import datetime

from pydantic import BaseModel, ConfigDict

from shared.enums import SenderEnum


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    chat_id: int


class AgentStepSchema(BaseModel):
    """A single tool call the agent made while producing its answer."""

    tool: str
    arguments: dict
    result: str


class SourceSchema(BaseModel):
    """A knowledge-base chunk used to ground the answer (RAG citation)."""

    title: str
    source: str


class MessageRead(MessageBase):
    id: int
    chat_id: int
    sender: SenderEnum
    created_at: datetime
    # Populated only for assistant messages.
    steps: list[AgentStepSchema] | None = None
    sources: list[SourceSchema] | None = None

    model_config = ConfigDict(from_attributes=True)
