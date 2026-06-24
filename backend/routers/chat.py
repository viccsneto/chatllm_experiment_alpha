from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, ChatSession, User
from backend.routers.auth import get_current_user
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


async def _generate_title(db: Session, user_message: str) -> str | None:
    """Tenta gerar um título curto chamando o modelo."""
    try:
        reply, _ = await generate_reply(
            user_message=(
                f"Gere um título muito curto (máximo 6 palavras, em português) "
                f"para uma conversa que começa com: {user_message}\n"
                f"Responda apenas com o título, sem aspas ou pontuação extra."
            ),
            history=[],
            model=None,
        )
        title = reply.strip().strip('"').strip("'")
        if len(title) > 100:
            title = title[:100]
        return title
    except Exception:
        return None


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    session_id = payload.session_id
    if session_id:
        sess = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
            .first()
        )
        if not sess:
            raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    else:
        sess = ChatSession(user_id=user.id)
        db.add(sess)
        db.commit()
        db.refresh(sess)
        session_id = sess.id

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

    db.add(ChatMessage(session_id=session_id, role="user", content=payload.message, model=resolved_model))
    db.add(ChatMessage(session_id=session_id, role="assistant", content=reply, model=resolved_model))

    # Auto-título se a sessão ainda não tiver
    if not sess.title:
        title = await _generate_title(db, payload.message)
        if title:
            sess.title = title

    sess.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT

    session_id = payload.session_id
    if session_id:
        sess = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
            .first()
        )
        if not sess:
            raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    else:
        sess = ChatSession(user_id=user.id)
        db.add(sess)
        db.commit()
        db.refresh(sess)
        session_id = sess.id

    async def event_generator():
        nonlocal session_id
        full_reply = ""
        try:
            async for delta in stream_reply(
                user_message=payload.message,
                history=[item.model_dump() for item in payload.history],
                model=payload.model,
            ):
                full_reply += delta
                yield f"data: {json.dumps({'delta': delta, 'session_id': session_id}, ensure_ascii=True)}\n\n"
        except OpenRouterConfigError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return
        except RuntimeError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return

        if full_reply.strip():
            db.add(
                ChatMessage(
                    session_id=session_id,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )

            if not sess.title:
                title = await _generate_title(db, payload.message)
                if title:
                    sess.title = title

            sess.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()

        yield f"data: {json.dumps({'done': True, 'session_id': session_id}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
