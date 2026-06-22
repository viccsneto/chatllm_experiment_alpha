from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.auth_utils import get_current_user
from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, ChatSession, User
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


TITLE_GENERATION_PROMPT = (
    "Gere um titulo curto (maximo 6 palavras) para esta conversa com base na primeira mensagem do usuario. "
    "Responda APENAS com o titulo, sem explicacoes, sem aspas, sem pontuacao extra."
)


def _get_or_create_session(db: Session, user_id: int, session_id: int | None) -> ChatSession:
    if session_id is not None:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        ).first()
        if session:
            return session
    # Create a new session
    session = ChatSession(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


async def _auto_title(session: ChatSession, user_message: str, db: Session) -> None:
    """Generate a title for the session if it still has the default name."""
    if session.title != "Nova conversa":
        return
    try:
        title, _ = await generate_reply(
            user_message=user_message,
            history=[],
            model=None,
            system_prompt=TITLE_GENERATION_PROMPT,
        )
        title = title.strip().strip('"').strip("'").strip(".").strip()
        if len(title) > 60:
            title = title[:60]
        if title:
            session.title = title
    except Exception:
        pass  # Silently fail — keep default title


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> ChatResponse:
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

    # Get or create session
    session = _get_or_create_session(db, current_user.id, payload.session_id)

    db.add(ChatMessage(user_id=current_user.id, session_id=session.id, session_key=str(session.id), role="user", content=payload.message, model=resolved_model))
    db.add(ChatMessage(user_id=current_user.id, session_id=session.id, session_key=str(session.id), role="assistant", content=reply, model=resolved_model))

    # Auto-generate title
    await _auto_title(session, payload.message, db)

    db.add(session)
    db.commit()

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> StreamingResponse:
    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT

    # Get or create session upfront so we have the session_id
    session = _get_or_create_session(db, current_user.id, payload.session_id)

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
                    user_id=current_user.id,
                    session_id=session.id,
                    session_key=str(session.id),
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    user_id=current_user.id,
                    session_id=session.id,
                    session_key=str(session.id),
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )

            # Auto-generate title from first user message
            await _auto_title(session, payload.message, db)

            # Ensure the session change is picked up by the ORM
            db.add(session)
            db.commit()

        yield f"data: {json.dumps({'done': True, 'session_id': session.id, 'session_title': session.title}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
