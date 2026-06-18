from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.auth import (
    AuthLoginRequest,
    AuthLogoutResponse,
    AuthRegisterRequest,
    AuthResponse,
    ErrorResponse,
)
from backend.services.auth import (
    authenticate_user,
    create_token,
    create_user,
    get_user_by_token,
    revoke_token,
)

router = APIRouter(tags=["auth"])


def _get_token_from_header(authorization: str | None = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticacao nao fornecido")
    return authorization[len("Bearer "):]


def get_current_user(
    db: Session = Depends(get_db),
    token_str: str = Depends(_get_token_from_header),
):
    user = get_user_by_token(db, token_str)
    if not user:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado")
    return user


@router.post("/api/auth/register", response_model=AuthResponse, responses={400: {"model": ErrorResponse}})
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)):
    try:
        user = create_user(db, email=payload.email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    token = create_token(db, user)
    return AuthResponse(token=token.token, email=user.email)


@router.post("/api/auth/login", response_model=AuthResponse, responses={401: {"model": ErrorResponse}})
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")

    token = create_token(db, user)
    return AuthResponse(token=token.token, email=user.email)


@router.post("/api/auth/logout", response_model=AuthLogoutResponse)
def logout(token_str: str = Depends(_get_token_from_header), db: Session = Depends(get_db)):
    revoke_token(db, token_str)
    return AuthLogoutResponse(message="Logout realizado com sucesso")


@router.get("/api/auth/me", response_model=AuthResponse)
def me(current_user=Depends(get_current_user)):
    return AuthResponse(token="", email=current_user.email)