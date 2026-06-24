from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    session_key: str
    title: str
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class CreateSessionRequest(BaseModel):
    session_key: str = Field(min_length=1, max_length=120)


class UpdateTitleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class ChatRequestWithSession(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_key: str = Field(min_length=1, max_length=120)
    model: str | None = None
    history: list[dict] = Field(default_factory=list)


class MessageResponse(BaseModel):
    role: str
    content: str
    model: str
    created_at: datetime


class MessageListResponse(BaseModel):
    session_key: str
    messages: list[MessageResponse]