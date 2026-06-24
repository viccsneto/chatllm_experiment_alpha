from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatSession, Session as AuthSession, User
from backend.schemas.session import (
    CreateSessionRequest,
    MessageListResponse,
    MessageResponse,
    SessionListResponse,
    SessionResponse,
    UpdateTitleRequest,
)

router = APIRouter()


def _get_user_from_token(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    """Extrai o usuario autenticado a partir do token no header Authorization."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou invalido.")
    token = authorization.removeprefix("Bearer ")

    auth_session = db.query(AuthSession).filter(AuthSession.token == token).first()
    if not auth_session:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado.")

    user = db.query(User).filter(User.id == auth_session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado.")

    return user


@router.get("/api/sessions", response_model=SessionListResponse)
def list_sessions(
    user: User = Depends(_get_user_from_token),
    db: Session = Depends(get_db),
) -> SessionListResponse:
    """Lista todas as sessoes do usuario, ordenadas pela mais recente."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return SessionListResponse(
        sessions=[
            SessionResponse(
                session_key=s.session_key,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ]
    )


@router.post("/api/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    payload: CreateSessionRequest,
    user: User = Depends(_get_user_from_token),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Cria uma nova sessao de chat para o usuario."""
    existing = db.query(ChatSession).filter(ChatSession.session_key == payload.session_key).first()
    if existing:
        raise HTTPException(status_code=409, detail="Esta sessao ja existe.")

    session = ChatSession(
        user_id=user.id,
        session_key=payload.session_key,
        title="Nova conversa",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionResponse(
        session_key=session.session_key,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.patch("/api/sessions/{session_key}/title", response_model=SessionResponse)
def update_title(
    session_key: str,
    payload: UpdateTitleRequest,
    user: User = Depends(_get_user_from_token),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Atualiza o titulo de uma sessao."""
    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_key == session_key, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")

    session.title = payload.title
    db.commit()
    db.refresh(session)

    return SessionResponse(
        session_key=session.session_key,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.delete("/api/sessions/{session_key}", status_code=200)
def delete_session(
    session_key: str,
    user: User = Depends(_get_user_from_token),
    db: Session = Depends(get_db),
) -> dict:
    """Deleta uma sessao e todas as suas mensagens."""
    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_key == session_key, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")

    from backend.models import ChatMessage
    db.query(ChatMessage).filter(ChatMessage.session_key == session_key).delete()
    db.delete(session)
    db.commit()
    return {"message": "Sessao deletada com sucesso."}


@router.get("/api/sessions/{session_key}/messages", response_model=MessageListResponse)
def get_session_messages(
    session_key: str,
    user: User = Depends(_get_user_from_token),
    db: Session = Depends(get_db),
) -> MessageListResponse:
    """Retorna todas as mensagens de uma sessao."""
    from backend.models import ChatMessage

    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_key == session_key, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_key == session_key)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return MessageListResponse(
        session_key=session_key,
        messages=[
            MessageResponse(
                role=m.role,
                content=m.content,
                model=m.model,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )