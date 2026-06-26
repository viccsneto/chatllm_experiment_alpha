from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
)
from backend.services.auth import (
    get_logged_in_email,
    login_user,
    logout_user,
    register_user,
)

router = APIRouter()


@router.post("/auth/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    try:
        user = register_user(db, email=payload.email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RegisterResponse(email=user.email)


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    try:
        token = login_user(db, email=payload.email, password=payload.password, device_fingerprint=payload.device_fingerprint)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return LoginResponse(email=payload.email, token=token)


@router.post("/auth/logout", response_model=LogoutResponse)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> LogoutResponse:
    try:
        logout_user(db, email=payload.email, token=payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LogoutResponse(message="Logout realizado com sucesso.")


@router.get("/auth/me", response_model=MeResponse)
def me(authorization: str | None = Header(None, alias="Authorization"), db: Session = Depends(get_db)) -> MeResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token nao informado.")
    token = authorization[7:]
    try:
        email = get_logged_in_email(db, token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return MeResponse(email=email)