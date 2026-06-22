from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    model: str | None = None
    session_key: str | None = None
    history: list[ChatMessageIn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    model: str
    session_key: str
    session_title: str


class ChatMessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatSessionListItem(BaseModel):
    key: str
    title: str | None
    created_at: datetime


class ChatSessionCreateResponse(BaseModel):
    key: str
    title: str | None


class ChatSessionDetailResponse(BaseModel):
    key: str
    title: str | None
    messages: list[ChatMessageOut]
