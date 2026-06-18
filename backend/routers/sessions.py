from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatMessage, ChatSession
from backend.schemas.session import SessionList, SessionMessagesOut, SessionOut
from backend.routers.auth import get_current_user
from backend.models import User

router = APIRouter()


@router.get("/api/sessions", response_model=SessionList)
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return SessionList(sessions=[SessionOut(id=s.id, title=s.title) for s in sessions])


@router.post("/api/sessions", response_model=SessionOut)
def create_session(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    session = ChatSession(id=session_id, user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionOut(id=session.id, title=session.title)


@router.get("/api/sessions/{session_id}/messages", response_model=SessionMessagesOut)
def get_session_messages(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_key == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return SessionMessagesOut(
        session_id=session_id,
        messages=[{"role": m.role, "content": m.content, "id": m.id} for m in messages],
    )


@router.put("/api/sessions/{session_id}/title")
def update_session_title(session_id: str, payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    title = payload.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Titulo nao pode ser vazio")
    session.title = title
    db.commit()
    return {"message": "Titulo atualizado"}


@router.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    db.delete(session)
    db.commit()
    return {"message": "Sessao removida"}