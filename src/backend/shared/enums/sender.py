from enum import Enum


class SenderEnum(str, Enum):
    USER = "user"
    LLM = "llm"
