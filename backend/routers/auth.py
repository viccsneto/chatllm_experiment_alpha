from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Session as SessionModel
from backend.models import User
from backend.schemas.auth import (
    AuthResponse,
    ErrorResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RegisterRequest,
)

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _generate_token() -> str:
    return secrets.token_hex(32)


@router.post(
    "/api/auth/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Cadastra um novo usuario com email e senha."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email ja esta cadastrado.",
        )

    hashed = pwd_context.hash(payload.password)
    user = User(email=payload.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = _generate_token()
    session = SessionModel(user_id=user.id, token=token)
    db.add(session)
    db.commit()

    return AuthResponse(token=token, email=user.email)


@router.post(
    "/api/auth/login",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse}},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Autentica um usuario existente com email e senha."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
        )

    if not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
        )

    token = _generate_token()
    session = SessionModel(user_id=user.id, token=token)
    db.add(session)
    db.commit()

    return AuthResponse(token=token, email=user.email)


@router.post(
    "/api/auth/logout",
    response_model=LogoutResponse,
    responses={401: {"model": ErrorResponse}},
)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> LogoutResponse:
    """Invalida o token de sessao do usuario."""
    session = (
        db.query(SessionModel)
        .filter(SessionModel.token == payload.token)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado.",
        )

    db.delete(session)
    db.commit()

    return LogoutResponse(message="Logout realizado com sucesso.")