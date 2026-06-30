from typing import Literal

from pydantic import BaseModel, Field

DocumentFormat = Literal["docx", "pdf"]


class DocumentExportRequest(BaseModel):
    format: DocumentFormat
    content: str = Field(min_length=1, max_length=100_000)
    title: str | None = Field(default=None, max_length=200)
    filename: str | None = Field(default=None, max_length=200)


class DocumentUploadResponse(BaseModel):
    filename: str
    pages: int
    chunks: int


class ChatDocumentInfo(BaseModel):
    filename: str
    chunks: int
