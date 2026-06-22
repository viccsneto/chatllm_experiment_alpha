from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.auth import SESSION_COOKIE_NAME, create_session_token, get_current_user, hash_password, verify_password
from backend.database import get_db
from backend.models import User, UserSession
from backend.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserInfoResponse

router = APIRouter()


@router.post("/api/auth/signup", response_model=AuthResponse)
def signup(request: SignupRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    existing_user = db.query(User).filter(User.email == request.email).one_or_none()
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Este email ja esta cadastrado.")

    user = User(email=request.email, password_hash=hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session_token()
    session = UserSession(user_id=user.id, token=token)
    db.add(session)
    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=7 * 24 * 60 * 60,
    )

    return AuthResponse(message="Cadastro realizado com sucesso.")


@router.post("/api/auth/login", response_model=AuthResponse)
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == request.email).one_or_none()
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha invalidos.")

    token = create_session_token()
    session = UserSession(user_id=user.id, token=token)
    db.add(session)
    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=7 * 24 * 60 * 60,
    )
    return AuthResponse(message="Login realizado com sucesso.")


@router.post("/api/auth/logout", response_model=AuthResponse)
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> AuthResponse:
    if session_token is None:
        raise HTTPException(status_code=401, detail="Nao autenticado.")

    session = db.query(UserSession).filter(UserSession.token == session_token, UserSession.revoked_at == None).one_or_none()
    if session is None:
        raise HTTPException(status_code=401, detail="Sessao invalida.")

    session.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(session)
    db.commit()

    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return AuthResponse(message="Logout realizado com sucesso.")


@router.get("/api/auth/me", response_model=UserInfoResponse)
def me(user: User = Depends(get_current_user)) -> UserInfoResponse:
    return UserInfoResponse(email=user.email)
