from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A mensagem não pode estar vazia.")
        return value


class CitationOut(BaseModel):
    section: str
    page: int
    source: str = "Manual de Políticas"


class ToolCallOut(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    ok: bool = True


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    citations: list[CitationOut] = Field(default_factory=list)
    handoff: bool = False
    tool_calls: list[ToolCallOut] = Field(default_factory=list)


class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime


class MessageOut(BaseModel):
    role: str
    content: str
    citations: list[CitationOut] = Field(default_factory=list)
    created_at: datetime | None = None


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[MessageOut] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    database: str
    llm: str
    mode: str
    version: str = "1.0.0"
    policy: str = "ok"
