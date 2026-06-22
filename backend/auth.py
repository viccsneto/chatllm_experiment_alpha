from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.config import (
    JWT_ALGORITHM,
    JWT_EXPIRY_HOURS,
    JWT_SECRET,
    LOGIN_BLOCK_MINUTES,
    MAX_LOGIN_ATTEMPTS,
)
from backend.database import get_db
from backend.models import User

security = HTTPBearer(auto_error=False)

# ── Rate limiting state (in-memory, resets on restart) ──
_login_attempts: dict[str, list[datetime]] = {}


def _clean_attempts(email: str) -> list[datetime]:
    """Remove attempts older than the block window and return remaining."""
    now = datetime.now(timezone.utc)
    window = now - timedelta(minutes=LOGIN_BLOCK_MINUTES)
    attempts = _login_attempts.get(email, [])
    attempts = [t for t in attempts if t > window]
    _login_attempts[email] = attempts
    return attempts


def check_login_blocked(email: str) -> None:
    attempts = _clean_attempts(email)
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Demasiadas tentativas. Tente novamente em {LOGIN_BLOCK_MINUTES} minutos.",
        )


def record_login_attempt(email: str) -> None:
    now = datetime.now(timezone.utc)
    _login_attempts.setdefault(email, []).append(now)


def reset_login_attempts(email: str) -> None:
    _login_attempts.pop(email, None)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(email: str) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {"sub": email, "exp": expiry, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticacao necessario.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalido.")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado. Faca login novamente.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalido.")

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado ou inativo.")
    return user