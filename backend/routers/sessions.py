from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as SQLSession
from sqlalchemy import desc

from backend.database import get_db
from backend.models import ChatMessage, Session, User
from backend.routers.chat import get_current_user
from backend.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionListResponse,
    SessionUpdate,
)
from backend.services.openrouter import generate_reply


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse)
def list_sessions(
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionListResponse:
    sessions = (
        db.query(Session)
        .filter(Session.user_id == current_user.id)
        .order_by(desc(Session.updated_at))
        .all()
    )
    return SessionListResponse(sessions=sessions)


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(
    payload: SessionCreate,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    session = Session(
        user_id=current_user.id,
        title=payload.title or "Nova conversa",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    session = db.query(Session).filter(
        Session.id == session_id, Session.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    return session


@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int,
    payload: SessionUpdate,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    session = db.query(Session).filter(
        Session.id == session_id, Session.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")

    if payload.title is not None:
        session.title = payload.title
    session.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}")
def delete_session(
    session_id: int,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    session = db.query(Session).filter(
        Session.id == session_id, Session.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")

    # Delete all messages in the session
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"message": "Sessao deletada com sucesso."}


@router.get("/{session_id}/messages")
def get_session_messages(
    session_id: int,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    session = db.query(Session).filter(
        Session.id == session_id, Session.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return {
        "session": {"id": session.id, "title": session.title},
        "messages": [
            {"id": msg.id, "role": msg.role, "content": msg.content, "created_at": msg.created_at.isoformat()}
            for msg in messages
        ],
    }


@router.post("/{session_id}/generate-title")
def generate_session_title(
    session_id: int,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    session = db.query(Session).filter(
        Session.id == session_id, Session.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")

    # Get the first user message to generate a title
    first_msg = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user",
        )
        .order_by(ChatMessage.created_at)
        .first()
    )

    if not first_msg:
        raise HTTPException(status_code=400, detail="Nenhuma mensagem na sessao para gerar titulo.")

    # Truncate first message for title generation
    title = first_msg.content[:60]
    if len(first_msg.content) > 60:
        title += "..."

    session.title = title
    session.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(session)

    return {"title": session.title}