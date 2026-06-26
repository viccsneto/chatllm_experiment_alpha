from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from backend.models import ChatMessage, ChatSession
from backend.services.openrouter import generate_reply


def create_session(db: DBSession, user_email: str) -> ChatSession:
    session = ChatSession(id=str(uuid.uuid4()), user_email=user_email)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_sessions(db: DBSession, user_email: str) -> list[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_email == user_email)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


def get_session(db: DBSession, session_id: str, user_email: str) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_email == user_email)
        .first()
    )


def get_session_messages(db: DBSession, session_id: str) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_key == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


async def auto_title(db: DBSession, session_id: str, first_message: str, first_reply: str) -> str | None:
    """Gera um titulo automatico para a sessao usando a IA."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is None or session.title is not None:
        return None

    try:
        title, _ = await generate_reply(
            user_message=(
                f"Generate a very short title (max 6 words) for this chat conversation:\n\n"
                f"User: {first_message}\n"
                f"Assistant: {first_reply[:500]}"
            ),
            history=[],
            model=None,
        )
        title = title.strip().strip('"').strip("'")
        if len(title) > 60:
            title = title[:60]
        session.title = title
        db.commit()
        return title
    except Exception:
        return None