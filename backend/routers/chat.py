from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, Session
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


def _get_or_create_session(db: Session, session_key: str | None) -> str:
    """Retorna session_key valida, criando uma nova sessao se necessario."""
    key = session_key or f"sess_{uuid.uuid4().hex[:12]}"
    existing = db.query(Session).filter(Session.session_key == key).first()
    if not existing:
        db.add(Session(session_key=key))
        db.commit()
    return key


def _generate_title_from_messages(db: Session, session_key: str) -> str:
    """Gera titulo a partir da primeira mensagem do usuario."""
    first_user_msg = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_key == session_key, ChatMessage.role == "user")
        .order_by(ChatMessage.created_at.asc())
        .first()
    )
    if first_user_msg:
        text = first_user_msg.content.strip()
        if len(text) > 55:
            return text[:55] + "..."
        return text
    return "Nova conversa"


def _ensure_session_title(db: Session, session_key: str) -> None:
    """Define o titulo automatico se a sessao ainda nao tiver um."""
    session = db.query(Session).filter(Session.session_key == session_key).first()
    if session and not session.title:
        session.title = _generate_title_from_messages(db, session_key)
        db.commit()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session_key = _get_or_create_session(db, payload.session_key)

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

    db.add(ChatMessage(session_key=session_key, role="user", content=payload.message, model=resolved_model))
    db.add(ChatMessage(session_key=session_key, role="assistant", content=reply, model=resolved_model))
    db.commit()

    _ensure_session_title(db, session_key)

    return ChatResponse(reply=reply, model=resolved_model, session_key=session_key)


@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    session_key = _get_or_create_session(db, payload.session_key)
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
                    session_key=session_key,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    session_key=session_key,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )
            db.commit()
            _ensure_session_title(db, session_key)

        yield f"data: {json.dumps({'done': True, 'session_key': session_key}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
