from __future__ import annotations

import json

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


def _generate_title_from_message(message: str) -> str:
    """Generate a concise title from the first user message."""
    clean = message.strip().replace("\n", " ")[:80]
    if len(clean) > 60:
        clean = clean[:57] + "..."
    return clean


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/sessions/{session_id}/messages")
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
) -> list[dict]:
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
    if current_user:
        query = query.filter(ChatMessage.user_id == current_user.id)
    messages = query.all()
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None}
        for m in messages
    ]


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db), current_user: User | None = Depends(get_current_user)) -> ChatResponse:
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
    user_id = current_user.id if current_user else None
    session_id = payload.session_id

    # Create session automatically if user is logged in and no session_id provided
    if user_id and not session_id:
        title = _generate_title_from_message(payload.message)
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        db.flush()
        session_id = session.id

    # Update title if session still has default title (only on first message)
    if session_id and user_id:
        existing = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
        if existing and existing.title == "Novo Chat":
            existing.title = _generate_title_from_message(payload.message)

    db.add(ChatMessage(session_key=str(session_id or "default"), session_id=session_id, role="user", content=payload.message, model=resolved_model, user_id=user_id))
    db.add(ChatMessage(session_key=str(session_id or "default"), session_id=session_id, role="assistant", content=reply, model=resolved_model, user_id=user_id))
    db.commit()

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest, db: Session = Depends(get_db), current_user: User | None = Depends(get_current_user)) -> StreamingResponse:
    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT

    async def event_generator():
        full_reply = ""
        user_id = current_user.id if current_user else None
        session_id = payload.session_id
        session_created = False

        # Create session automatically if user is logged in and no session_id
        if user_id and not session_id:
            title = _generate_title_from_message(payload.message)
            session = ChatSession(user_id=user_id, title=title)
            db.add(session)
            db.flush()
            session_id = session.id
            session_created = True

        try:
            async for delta in stream_reply(
                user_message=payload.message,
                history=[item.model_dump() for item in payload.history],
                model=payload.model,
            ):
                full_reply += delta
                yield f"data: {json.dumps({'delta': delta, 'session_id': session_id} if session_id else {'delta': delta}, ensure_ascii=True)}\n\n"
        except OpenRouterConfigError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return
        except RuntimeError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return

        if full_reply.strip():
            # Update title if still default
            if session_id and user_id and not session_created:
                existing = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
                if existing and existing.title == "Novo Chat":
                    existing.title = _generate_title_from_message(payload.message)

            db.add(
                ChatMessage(
                    session_key=str(session_id or "default"),
                    session_id=session_id,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                    user_id=user_id,
                )
            )
            db.add(
                ChatMessage(
                    session_key=str(session_id or "default"),
                    session_id=session_id,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                    user_id=user_id,
                )
            )
            db.commit()

        yield f"data: {json.dumps({'done': True, 'session_id': session_id} if session_id else {'done': True}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
