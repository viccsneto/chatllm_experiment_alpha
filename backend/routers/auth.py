from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Session, User
from backend.schemas.auth import AuthResponse, LoginRequest, LogoutResponse, SignupRequest, UserInfo


router = APIRouter(tags=["auth"])

security = HTTPBearer(auto_error=False)

SESSION_DURATION = timedelta(days=7)


def _hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the authenticated User or None if no valid token."""
    if credentials is None:
        return None
    token_str = credentials.credentials
    session = (
        db.query(Session)
        .filter(
            Session.token == token_str,
            Session.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if session is None:
        return None
    user = db.query(User).filter(User.id == session.user_id).first()
    return user


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Return the authenticated User or raise 401."""
    user = get_current_user(credentials, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/api/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        hashed_password=_hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = _generate_token()
    session = Session(
        token=token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + SESSION_DURATION,
    )
    db.add(session)
    db.commit()

    return AuthResponse(message="Account created successfully", token=token)


@router.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not _verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = _generate_token()
    session = Session(
        token=token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + SESSION_DURATION,
    )
    db.add(session)
    db.commit()

    return AuthResponse(message="Login successful", token=token)


@router.post("/api/auth/logout", response_model=LogoutResponse)
def logout(
    current_user: User = Depends(require_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    """Invalidate the current session token."""
    db.query(Session).filter(Session.token == credentials.credentials).delete()
    db.commit()
    return LogoutResponse(message="Logged out successfully")


@router.get("/api/auth/me", response_model=UserInfo)
def me(current_user: User = Depends(require_user)) -> UserInfo:
    return UserInfo(id=current_user.id, email=current_user.email)
