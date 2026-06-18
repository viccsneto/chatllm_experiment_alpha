from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    pass


class SessionOut(BaseModel):
    id: str
    title: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionList(BaseModel):
    sessions: list[SessionOut]


class SessionMessagesOut(BaseModel):
    session_id: str
    messages: list[dict]


class SessionTitleUpdate(BaseModel):
    title: str