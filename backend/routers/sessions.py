from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from backend.database import get_db
from backend.models import ChatMessage, Session
from backend.schemas.session import SessionCreate, SessionListResponse, SessionResponse, SessionUpdate


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _generate_title(messages: list[ChatMessage]) -> str:
    """Gera um titulo a partir da primeira mensagem do usuario."""
    for msg in messages:
        if msg.role == "user":
            text = msg.content.strip()
            if len(text) > 55:
                return text[:55] + "..."
            return text
    return "Nova conversa"


@router.get("", response_model=SessionListResponse)
def list_sessions(db: DBSession = Depends(get_db)) -> SessionListResponse:
    sessions = (
        db.query(Session)
        .order_by(Session.updated_at.desc())
        .all()
    )
    return SessionListResponse(sessions=sessions)


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, db: DBSession = Depends(get_db)) -> SessionResponse:
    existing = db.query(Session).filter(Session.session_key == payload.session_key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session key ja existe.",
        )
    session = Session(session_key=payload.session_key)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_key}", response_model=SessionResponse)
def update_session(session_key: str, payload: SessionUpdate, db: DBSession = Depends(get_db)) -> SessionResponse:
    session = db.query(Session).filter(Session.session_key == session_key).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session nao encontrada.")
    if payload.title is not None:
        session.title = payload.title
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_key}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_session(session_key: str, db: DBSession = Depends(get_db)) -> None:
    session = db.query(Session).filter(Session.session_key == session_key).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session nao encontrada.")
    db.delete(session)
    db.commit()


@router.get("/{session_key}/messages")
def get_session_messages(session_key: str, db: DBSession = Depends(get_db)) -> list[dict]:
    session = db.query(Session).filter(Session.session_key == session_key).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session nao encontrada.")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_key == session_key)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {"id": msg.id, "role": msg.role, "content": msg.content, "created_at": msg.created_at.isoformat()}
        for msg in messages
    ]


@router.post("/{session_key}/auto-title", response_model=SessionResponse)
def auto_title(session_key: str, db: DBSession = Depends(get_db)) -> SessionResponse:
    """Gera ou atualiza o titulo da sessao baseado na primeira mensagem do usuario."""
    session = db.query(Session).filter(Session.session_key == session_key).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session nao encontrada.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_key == session_key)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    if not messages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhuma mensagem para gerar titulo.")

    session.title = _generate_title(messages)
    db.commit()
    db.refresh(session)
    return session