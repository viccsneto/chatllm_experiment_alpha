from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth_utils import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.database import get_db
from backend.models import User
from backend.schemas.auth import AuthResponse, LoginRequest, RegisterRequest


router = APIRouter(tags=["auth"])


@router.post("/api/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email invalido.")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email ja cadastrado.")

    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter no minimo 6 caracteres.")

    user = User(email=email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.email)
    return AuthResponse(access_token=token, email=user.email)


@router.post("/api/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada.")

    token = create_access_token(user.email)
    return AuthResponse(access_token=token, email=user.email)


@router.post("/api/logout")
def logout() -> dict[str, str]:
    # Stateless JWT: logout é tratado no frontend descartando o token.
    # Em produção, poderia usar uma blacklist de tokens.
    return {"message": "Logout realizado com sucesso."}


@router.get("/api/me", response_model=dict)
def me(current_user: User = Depends(get_current_user)) -> dict:
    return {"id": current_user.id, "email": current_user.email}