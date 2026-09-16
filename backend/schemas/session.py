from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    session_key: str


class SessionUpdate(BaseModel):
    title: str | None = None


class SessionResponse(BaseModel):
    id: int
    session_key: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]