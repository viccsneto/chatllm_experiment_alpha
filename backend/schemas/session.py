from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    user_email: str = Field(min_length=1, max_length=255)


class SessionCreateResponse(BaseModel):
    id: str
    title: str | None = None


class SessionListItem(BaseModel):
    id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionListItem]


class SessionRenameResponse(BaseModel):
    id: str
    title: str