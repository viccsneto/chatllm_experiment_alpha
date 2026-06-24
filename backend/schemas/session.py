from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    pass


class SessionResponse(BaseModel):
    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionTitleUpdate(BaseModel):
    title: str


class ChatMessageOut(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    model: str
    created_at: datetime

    model_config = {"from_attributes": True}