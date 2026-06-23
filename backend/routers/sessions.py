from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession

from backend.database import get_db
from backend.models import ChatMessage, ChatSession as ChatSessionModel
from backend.schemas.session import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionListItem,
    SessionListResponse,
)
from backend.services.auth import get_logged_in_email
from backend.services.session import (
    create_session,
    get_session_messages,
    list_sessions,
    get_session,
)

router = APIRouter()


def _resolve_user(authorization: str | None, db: DBSession) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token nao informado.")
    token = authorization[7:]
    try:
        return get_logged_in_email(db, token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/api/sessions", response_model=SessionCreateResponse, status_code=201)
def create(
    payload: SessionCreateRequest,
    authorization: str | None = Header(None, alias="Authorization"),
    db: DBSession = Depends(get_db),
) -> SessionCreateResponse:
    user_email = _resolve_user(authorization, db)
    if payload.user_email != user_email:
        raise HTTPException(status_code=403, detail="Email nao corresponde ao token.")
    session = create_session(db, user_email=user_email)
    return SessionCreateResponse(id=session.id, title=session.title)


@router.get("/api/sessions", response_model=SessionListResponse)
def list_all(
    user_email: str,
    authorization: str | None = Header(None, alias="Authorization"),
    db: DBSession = Depends(get_db),
) -> SessionListResponse:
    authed_email = _resolve_user(authorization, db)
    if user_email != authed_email:
        raise HTTPException(status_code=403, detail="Email nao corresponde ao token.")
    sessions = list_sessions(db, user_email=user_email)
    items = [
        SessionListItem(id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at)
        for s in sessions
    ]
    return SessionListResponse(sessions=items)


@router.get("/api/sessions/{session_id}/messages")
def list_messages(
    session_id: str,
    user_email: str,
    authorization: str | None = Header(None, alias="Authorization"),
    db: DBSession = Depends(get_db),
):
    authed_email = _resolve_user(authorization, db)
    if user_email != authed_email:
        raise HTTPException(status_code=403, detail="Email nao corresponde ao token.")
    session = get_session(db, session_id, user_email)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    messages = get_session_messages(db, session_id)
    return [
        {"role": msg.role, "content": msg.content, "created_at": msg.created_at.isoformat()}
        for msg in messages
    ]


@router.delete("/api/sessions/{session_id}", status_code=204)
def delete(
    session_id: str,
    user_email: str,
    authorization: str | None = Header(None, alias="Authorization"),
    db: DBSession = Depends(get_db),
):
    authed_email = _resolve_user(authorization, db)
    if user_email != authed_email:
        raise HTTPException(status_code=403, detail="Email nao corresponde ao token.")
    session = get_session(db, session_id, user_email)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    db.query(ChatMessage).filter(ChatMessage.session_key == session_id).delete()
    db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).delete()
    db.commit()