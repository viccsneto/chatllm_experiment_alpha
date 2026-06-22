from __future__ import annotations

import json

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, ChatSession, User
from backend.schemas.chat import (
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    ChatSessionCreateResponse,
    ChatSessionDetailResponse,
    ChatSessionListItem,
)
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


def _derive_session_title(reply: str) -> str:
    text = reply.strip().splitlines()[0].strip()
    if not text:
        return "Nova conversa"

    if len(text) <= 60:
        return text

    shortened = text[:60].rsplit(" ", 1)[0]
    return shortened or text[:60]


def _get_user_session_by_key(db: Session, user: User, session_key: str) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id, ChatSession.key == session_key)
        .one_or_none()
    )


def _get_or_create_current_session(db: Session, user: User) -> ChatSession:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.asc())
        .first()
    )
    if session is not None:
        return session

    generated_key = uuid4().hex
    session = ChatSession(user_id=user.id, key=generated_key)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _ensure_session_title(db: Session, session: ChatSession, assistant_reply: str) -> str:
    if session.title is not None:
        return session.title

    session.title = _derive_session_title(assistant_reply)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session.title


@router.get("/api/chat/sessions", response_model=list[ChatSessionListItem])
def list_chat_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ChatSessionListItem]:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [
        ChatSessionListItem(key=session.key, title=session.title, created_at=session.created_at)
        for session in sessions
    ]


@router.post("/api/chat/sessions", response_model=ChatSessionCreateResponse)
def create_chat_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatSessionCreateResponse:
    generated_key = uuid4().hex
    session = ChatSession(user_id=user.id, key=generated_key)
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatSessionCreateResponse(key=session.key, title=session.title)


@router.get("/api/chat/sessions/{session_key}", response_model=ChatSessionDetailResponse)
def get_chat_session(
    session_key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatSessionDetailResponse:
    session = _get_user_session_by_key(db, user, session_key)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao de chat nao encontrada.")

    messages = [
        ChatMessageOut(role=message.role, content=message.content)
        for message in (
            db.query(ChatMessage)
            .filter(ChatMessage.session_key == session.key)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
    ]
    return ChatSessionDetailResponse(
        key=session.key,
        title=session.title,
        messages=messages,
    )


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    session = (
        _get_user_session_by_key(db, user, payload.session_key)
        if payload.session_key
        else _get_or_create_current_session(db, user)
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao de chat nao encontrada.")

    try:
        reply, model_name = await generate_reply(
            user_message=payload.message,
            history=[item.model_dump() for item in payload.history],
            model=payload.model,
        )
    except OpenRouterConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    resolved_model = payload.model or model_name or OPENROUTER_MODEL_DEFAULT

    db.add(
        ChatMessage(
            session_key=session.key,
            role="user",
            content=payload.message,
            model=resolved_model,
        )
    )
    db.add(
        ChatMessage(
            session_key=session.key,
            role="assistant",
            content=reply,
            model=resolved_model,
        )
    )
    db.commit()

    session_title = _ensure_session_title(db, session, reply)

    return ChatResponse(
        reply=reply,
        model=resolved_model,
        session_key=session.key,
        session_title=session_title,
    )


@router.post("/api/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    session = (
        _get_user_session_by_key(db, user, payload.session_key)
        if payload.session_key
        else _get_or_create_current_session(db, user)
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao de chat nao encontrada.")

    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT

    async def event_generator():
        full_reply = ""
        try:
            async for delta in stream_reply(
                user_message=payload.message,
                history=[item.model_dump() for item in payload.history],
                model=payload.model,
            ):
                full_reply += delta
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=True)}\n\n"
        except OpenRouterConfigError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return
        except RuntimeError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return

        if full_reply.strip():
            db.add(
                ChatMessage(
                    session_key=session.key,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    session_key=session.key,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )
            db.commit()
            _ensure_session_title(db, session, full_reply)

        yield f"data: {json.dumps({'done': True, 'session_key': session.key, 'session_title': session.title}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
