from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatMessage, ChatSession
from backend.routers.auth import require_user
from backend.schemas.session import SessionCreate, SessionOut, SessionRename
from backend.schemas.chat import ChatMessageIn


router = APIRouter(tags=["sessions"])


def _generate_title_from_messages(messages: list[ChatMessage]) -> str:
    """Generate a title from the first user message content."""
    for msg in messages:
        if msg.role == "user":
            text = msg.content.strip()
            if text:
                # Truncate to first ~50 chars
                return text[:50] + ("..." if len(text) > 50 else "")
    return "Nova conversa"


@router.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(require_user),
) -> list[SessionOut]:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return sessions


@router.post("/api/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_user),
) -> SessionOut:
    session = ChatSession(
        user_id=current_user.id,
        title="Nova conversa",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/api/sessions/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_user),
) -> SessionOut:
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/api/sessions/{session_id}", response_model=SessionOut)
def rename_session(
    session_id: int,
    payload: SessionRename,
    db: Session = Depends(get_db),
    current_user=Depends(require_user),
) -> SessionOut:
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = payload.title
    session.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/api/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_user),
) -> Response:
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/sessions/{session_id}/messages", response_model=list[ChatMessageIn])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_user),
) -> list[ChatMessageIn]:
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        ChatMessageIn(role=msg.role, content=msg.content)
        for msg in messages
    ]


@router.post("/api/sessions/{session_id}/auto-title", response_model=SessionOut)
def auto_title_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_user),
) -> SessionOut:
    """Auto-generate title from the first user message in the session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    new_title = _generate_title_from_messages(messages)
    session.title = new_title
    session.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(session)
    return session