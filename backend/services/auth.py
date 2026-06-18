from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.orm import Session

from backend.models import AuthToken, User

TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str) -> User:
    existing = get_user_by_email(db, email)
    if existing:
        raise ValueError("Email ja cadastrado")

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_token(db: Session, user: User) -> AuthToken:
    token_str = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=TOKEN_EXPIRE_DAYS)
    token = AuthToken(user_id=user.id, token=token_str, expires_at=expires_at)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_user_by_token(db: Session, token_str: str) -> User | None:
    token = (
        db.query(AuthToken)
        .filter(
            AuthToken.token == token_str,
            AuthToken.is_revoked == False,
            AuthToken.expires_at > datetime.now(timezone.utc).replace(tzinfo=None),
        )
        .first()
    )
    if not token:
        return None
    user = db.query(User).filter(User.id == token.user_id, User.is_active == True).first()
    return user


def revoke_token(db: Session, token_str: str) -> bool:
    token = db.query(AuthToken).filter(AuthToken.token == token_str).first()
    if not token:
        return False
    token.is_revoked = True
    db.commit()
    return True