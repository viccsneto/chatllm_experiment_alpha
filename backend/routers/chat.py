from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session as SQLSession

from backend.config import JWT_ALGORITHM, JWT_SECRET_KEY, OPENROUTER_MODEL_DEFAULT
from backend.database import SessionLocal, get_db
from backend.models import ChatMessage, Session, User
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


def get_current_user(request: Request, db: SQLSession = Depends(get_db)) -> User:
    """Extract and verify JWT from Authorization header, return user or 401."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de acesso nao fornecido.")

    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalido.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado.")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado.")
    return user


def get_or_create_session(db: SQLSession, user_id: int, session_id: int | None) -> Session:
    """Get existing session or create a new one for the user."""
    if session_id:
        session = db.query(Session).filter(
            Session.id == session_id, Session.user_id == user_id
        ).first()
        if session:
            session.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            return session

    # Create new session
    session = Session(user_id=user_id, title="Nova conversa")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)) -> dict:
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    session = get_or_create_session(db, current_user.id, payload.session_id)

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
            session_id=session.id,
            role="user",
            content=payload.message,
            model=resolved_model,
            user_id=current_user.id,
        )
    )
    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            content=reply,
            model=resolved_model,
            user_id=current_user.id,
        )
    )
    db.commit()

    return ChatResponse(reply=reply, model=resolved_model, session_id=session.id)


@router.post("/api/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    db: SQLSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    session = get_or_create_session(db, current_user.id, payload.session_id)
    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT

    # Save user message immediately so the session is never empty
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.message,
        model=resolved_model,
        user_id=current_user.id,
    )
    db.add(user_msg)
    db.commit()
    session_id_value = session.id
    user_id_value = current_user.id

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
            yield f"data: {json.dumps({'done': True, 'session_id': session_id_value}, ensure_ascii=True)}\n\n"
            return
        except RuntimeError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            yield f"data: {json.dumps({'done': True, 'session_id': session_id_value}, ensure_ascii=True)}\n\n"
            return

        if full_reply.strip():
            # Use a new session to save the reply, since the db from Depends
            # may be closed by the time the async generator runs.
            try:
                save_db = SessionLocal()
                save_db.add(
                    ChatMessage(
                        session_id=session_id_value,
                        role="assistant",
                        content=full_reply,
                        model=resolved_model,
                        user_id=user_id_value,
                    )
                )
                save_db.commit()
            finally:
                save_db.close()

        yield f"data: {json.dumps({'done': True, 'session_id': session_id_value}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
