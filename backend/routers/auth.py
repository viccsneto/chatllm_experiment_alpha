from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import (
    check_login_blocked,
    create_token,
    get_current_user,
    hash_password,
    record_login_attempt,
    reset_login_attempts,
    verify_password,
)
from backend.database import get_db
from backend.models import User
from backend.schemas.auth import AuthResponse, LoginRequest, LogoutResponse, MeResponse, RegisterRequest

router = APIRouter(tags=["auth"])


@router.post("/api/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email ja cadastrado.")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.email)
    return AuthResponse(token=token, email=user.email)


@router.post("/api/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    check_login_blocked(payload.email)

    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        record_login_attempt(payload.email)
        raise HTTPException(status_code=401, detail="Email ou senha incorretos.")

    reset_login_attempts(payload.email)
    token = create_token(user.email)
    return AuthResponse(token=token, email=user.email)


@router.post("/api/logout", response_model=LogoutResponse)
def logout(current_user: User = Depends(get_current_user)) -> LogoutResponse:
    # O logout é gerido pelo frontend (remove o token).
    # O backend apenas confirma que o token era válido.
    return LogoutResponse(message="Logout realizado com sucesso.")


@router.get("/api/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(email=current_user.email, id=current_user.id)