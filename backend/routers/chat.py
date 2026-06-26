from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, ChatSession
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.auth import get_logged_in_email
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply
from backend.services.session import auto_title, create_session, get_session


router = APIRouter()


def _resolve_user(authorization: str | None, db: Session) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token nao informado.")
    token = authorization[7:]
    try:
        return get_logged_in_email(db, token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


async def _persist_and_title(db: Session, session_id: str, user_msg: str, reply: str, model: str) -> str | None:
    db.add(ChatMessage(session_key=session_id, role="user", content=user_msg, model=model))
    db.add(ChatMessage(session_key=session_id, role="assistant", content=reply, model=model))
    db.commit()

    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if chat_session and chat_session.title is None:
        return await auto_title(db, session_id, user_msg, reply)
    return chat_session.title if chat_session else None


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> ChatResponse:
    user_email = _resolve_user(authorization, db)

    session_id = payload.session_id
    if session_id:
        session = get_session(db, session_id, user_email)
        if session is None:
            raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    else:
        session = create_session(db, user_email)
        session_id = session.id

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
    title = await _persist_and_title(db, session_id, payload.message, reply, resolved_model)

    return ChatResponse(reply=reply, model=resolved_model, session_id=session_id, title=title)


@router.post("/api/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    user_email = _resolve_user(authorization, db)

    session_id = payload.session_id
    if session_id:
        session = get_session(db, session_id, user_email)
        if session is None:
            raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    else:
        session = create_session(db, user_email)
        session_id = session.id

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
                yield f"data: {json.dumps({'delta': delta, 'session_id': session_id}, ensure_ascii=True)}\n\n"
        except OpenRouterConfigError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return
        except RuntimeError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return

        if full_reply.strip():
            title = await _persist_and_title(db, session_id, payload.message, full_reply, resolved_model)
            yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'title': title}, ensure_ascii=True)}\n\n"
        else:
            yield f"data: {json.dumps({'done': True, 'session_id': session_id}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
