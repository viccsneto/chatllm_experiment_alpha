from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, ChatSession
from backend.routers.auth import get_current_user
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.openrouter import (
    OpenRouterConfigError,
    generate_reply,
    generate_title,
    stream_reply,
)


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ChatResponse:
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

    db.add(ChatMessage(session_key="default", session_id=payload.session_id, role="user", content=payload.message, model=resolved_model))
    db.add(ChatMessage(session_key="default", session_id=payload.session_id, role="assistant", content=reply, model=resolved_model))
    db.commit()

    # Generate automatic title if session has no title yet
    if payload.session_id is not None:
        session = (
            db.query(ChatSession)
            .filter(
                ChatSession.id == payload.session_id,
                ChatSession.user_id == current_user.id,
            )
            .first()
        )
        if session and not session.title:
            try:
                session_title = await generate_title(
                    user_message=payload.message, model=payload.model
                )
                session.title = session_title
                db.commit()
            except Exception:
                pass

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> StreamingResponse:
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
            msg_user = ChatMessage(
                session_key="default",
                session_id=payload.session_id,
                role="user",
                content=payload.message,
                model=resolved_model,
            )
            msg_assistant = ChatMessage(
                session_key="default",
                session_id=payload.session_id,
                role="assistant",
                content=full_reply,
                model=resolved_model,
            )
            db.add(msg_user)
            db.add(msg_assistant)
            db.commit()

            # Generate automatic title if session has no title yet
            if payload.session_id is not None:
                session = (
                    db.query(ChatSession)
                    .filter(
                        ChatSession.id == payload.session_id,
                        ChatSession.user_id == current_user.id,
                    )
                    .first()
                )
                if session and not session.title:
                    try:
                        session_title = await generate_title(
                            user_message=payload.message, model=payload.model
                        )
                        session.title = session_title
                        db.commit()
                    except Exception:
                        pass  # Non-critical, keep session without title

            yield f"data: {json.dumps({'done': True}, ensure_ascii=True)}\n\n"
            return

        yield f"data: {json.dumps({'done': True}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
