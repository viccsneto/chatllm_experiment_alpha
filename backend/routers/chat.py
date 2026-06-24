from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, ChatSession
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.schemas.session import ChatRequestWithSession
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
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

    db.add(ChatMessage(session_key="default", role="user", content=payload.message, model=resolved_model))
    db.add(ChatMessage(session_key="default", role="assistant", content=reply, model=resolved_model))
    db.commit()

    return ChatResponse(reply=reply, model=resolved_model)


def _generate_title(user_message: str, reply: str) -> str:
    """Gera um titulo curto a partir da primeira mensagem do usuario e resposta."""
    # Pega as primeiras palavras da mensagem do usuario como titulo
    max_words = 8
    words = user_message.strip().split()
    if len(words) <= max_words:
        base = user_message.strip()
    else:
        base = " ".join(words[:max_words]) + "..."

    # Limita o tamanho do titulo
    if len(base) > 100:
        base = base[:97] + "..."
    return base


@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequestWithSession, db: Session = Depends(get_db)) -> StreamingResponse:
    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT

    async def event_generator():
        full_reply = ""
        try:
            async for delta in stream_reply(
                user_message=payload.message,
                history=payload.history,
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
                    session_key=payload.session_key,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    session_key=payload.session_key,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )

            # Atualiza updated_at da sessao e gera titulo se for a primeira mensagem
            session = db.query(ChatSession).filter(ChatSession.session_key == payload.session_key).first()
            if session:
                if session.title == "Nova conversa":
                    session.title = _generate_title(payload.message, full_reply)
                from datetime import datetime, timezone
                session.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

            db.commit()

        yield f"data: {json.dumps({'done': True, 'title': session.title if session else None}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
