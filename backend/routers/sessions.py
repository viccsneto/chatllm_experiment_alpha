from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatMessage, ChatSession, User
from backend.routers.auth import get_current_user
from backend.schemas.session import (
    ChatMessageOut,
    SessionCreate,
    SessionResponse,
    SessionTitleUpdate,
)

router = APIRouter()


def _session_to_response(s: ChatSession) -> SessionResponse:
    return SessionResponse(
        id=s.id,
        title=s.title,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.get("/api/sessions", response_model=list[SessionResponse])
def list_sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SessionResponse]:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [_session_to_response(s) for s in sessions]


@router.post("/api/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    _body: SessionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionResponse:
    session = ChatSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_to_response(session)


@router.delete("/api/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessao nao encontrada.")
    db.delete(session)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def list_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatMessageOut]:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessao nao encontrada.")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [
        ChatMessageOut(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            model=m.model,
            created_at=m.created_at,
        )
        for m in messages
    ]