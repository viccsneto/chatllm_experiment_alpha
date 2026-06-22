from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session as DBSession

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import ChatMessage, Session, User
from backend.schemas.session import SessionCreate, SessionListResponse, SessionMessagesResponse, SessionResponse

router = APIRouter(tags=["sessions"])


@router.get("/api/sessions", response_model=SessionListResponse)
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> SessionListResponse:
    sessions = (
        db.query(Session)
        .filter(Session.user_id == current_user.id)
        .order_by(Session.updated_at.desc())
        .all()
    )
    result = []
    for s in sessions:
        msg_count = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
        result.append(
            SessionResponse(
                id=s.id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=msg_count,
            )
        )
    return SessionListResponse(sessions=result)


@router.post("/api/sessions", response_model=SessionResponse)
def create_session(
    payload: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> SessionResponse:
    session = Session(user_id=current_user.id, title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.delete("/api/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> Response:
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    db.delete(session)
    db.commit()
    return Response(status_code=204)


@router.get("/api/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
) -> SessionMessagesResponse:
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return SessionMessagesResponse(
        messages=[
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages
        ]
    )