from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY
from backend.database import get_db
from backend.models import User
from backend.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    SecurityQuestionResponse,
    SignUpRequest,
    VerifySecurityAnswerRequest,
)
from jose import JWTError, jwt
from passlib.context import CryptContext


router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    db: Session = Depends(get_db), token: str | None = None
) -> User | None:
    """Extract token from various sources and return the authenticated user or None."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    return user


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email ja esta cadastrado.",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        security_question=payload.security_question,
        hashed_security_answer=hash_password(payload.security_answer.lower().strip()),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return AuthResponse(
        access_token=token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
        )

    token = create_access_token(user.id, user.email)
    return AuthResponse(
        access_token=token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    )


@router.post("/forgot-password", response_model=SecurityQuestionResponse)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> SecurityQuestionResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email nao encontrado.",
        )

    return SecurityQuestionResponse(security_question=user.security_question)


@router.post("/verify-security-answer", response_model=MessageResponse)
def verify_security_answer(
    payload: VerifySecurityAnswerRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email nao encontrado.",
        )

    if not verify_password(payload.security_answer.lower().strip(), user.hashed_security_answer):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Resposta de seguranca incorreta.",
        )

    return MessageResponse(message="Resposta correta. Ja pode redefinir sua senha.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email nao encontrado.",
        )

    user.hashed_password = hash_password(payload.new_password)
    db.commit()

    return MessageResponse(message="Senha redefinida com sucesso.")


@router.post("/logout", response_model=MessageResponse)
def logout() -> MessageResponse:
    return MessageResponse(message="Logout realizado com sucesso.")