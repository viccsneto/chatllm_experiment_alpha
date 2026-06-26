from __future__ import annotations

import hashlib
import hmac
import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.config import SERVER_SECRET_HASH
from backend.models import DeviceSession, HashingKey, User

TOKEN_EXPIRY_DAYS = 7


# ── Key management ──────────────────────────────────────────────


def _ensure_active_key(db: Session) -> HashingKey:
    """Retorna a chave ativa atual; cria uma nova se nao existir."""
    key = db.query(HashingKey).filter(HashingKey.active.is_(True)).first()
    if key is not None:
        return key

    key_id = uuid.uuid4().hex[:12]
    key_value = hashlib.sha256(f"{SERVER_SECRET_HASH}:{key_id}".encode()).hexdigest()
    key = HashingKey(key_id=key_id, key_value=key_value, active=True)
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


def _lookup_key_by_id(db: Session, key_id: str) -> HashingKey | None:
    return db.query(HashingKey).filter(HashingKey.key_id == key_id).first()


# ── Hashing ─────────────────────────────────────────────────────


def _compute_hash(key_value: str, email: str, password: str) -> str:
    return hmac.new(
        key_value.encode(),
        f"{email}:{password}".encode(),
        hashlib.sha256,
    ).hexdigest()


# ── Timing-safe comparison ──────────────────────────────────────


def _time_safe_equal(a: str, b: str) -> bool:
    """Comparacao de tempo constante para evitar timing attacks."""
    return hmac.compare_digest(a, b)


def _verify_hash(stored_hash: str, email: str, password: str, db: Session) -> bool:
    """Verifica o hash com protecao contra timing attack.

    Fluxo:
    1. Extrai key_id do hash armazenado (formato: 'key_id:hash')
    2. Busca a chave correspondente no banco
    3. Recalcula HMAC(email, password) com aquela chave
    4. Compara com tempo constante — mesmo se comprimentos forem diferentes,
       executa !timeSafeEqual para nao vazar informacao via tempo de resposta.
    """
    if ":" not in stored_hash:
        return False

    key_id, actual_hash = stored_hash.split(":", 1)
    key = _lookup_key_by_id(db, key_id)
    if key is None:
        return False

    expected = _compute_hash(key.key_value, email, password)

    return _time_safe_equal(expected, actual_hash)


# ── Email validation ────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$")


def _validate_email(email: str) -> None:
    if not _EMAIL_RE.match(email):
        raise ValueError("Email invalido.")


# ── Public API ──────────────────────────────────────────────────


def register_user(db: Session, email: str, password: str) -> User:
    """Cadastra um novo usuario. Dispara ValueError se email invalido ou ja existir."""
    _validate_email(email)
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise ValueError("Email ja cadastrado.")

    active_key = _ensure_active_key(db)
    hash_value = _compute_hash(active_key.key_value, email, password)
    stored = f"{active_key.key_id}:{hash_value}"

    user = User(email=email, password_hash=stored)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str, device_fingerprint: str) -> str:
    """Autentica o usuario e retorna um token de sessao.

    Dispara ValueError se email invalido, inexistente ou senha incorreta.
    """
    _validate_email(email)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise ValueError("Email ou senha incorretos.")

    if not _verify_hash(user.password_hash, email, password, db):
        raise ValueError("Email ou senha incorretos.")

    # Inativa sessoes anteriores para este dispositivo
    db.query(DeviceSession).filter(
        DeviceSession.email == email,
        DeviceSession.device_fingerprint == device_fingerprint,
        DeviceSession.logged_in.is_(True),
    ).update({"logged_in": False})
    db.commit()

    token = str(uuid.uuid4())
    session = DeviceSession(
        email=email,
        device_fingerprint=device_fingerprint,
        token=token,
        logged_in=True,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=TOKEN_EXPIRY_DAYS),
    )
    db.add(session)
    db.commit()
    return token


def logout_user(db: Session, email: str, token: str) -> None:
    """Marca a sessao como deslogada. Dispara ValueError se sessao nao existir."""
    session = (
        db.query(DeviceSession)
        .filter(
            DeviceSession.email == email,
            DeviceSession.token == token,
            DeviceSession.logged_in.is_(True),
        )
        .first()
    )
    if session is None:
        raise ValueError("Sessao nao encontrada ou ja encerrada.")

    session.logged_in = False
    db.commit()


def get_logged_in_email(db: Session, token: str) -> str:
    """Retorna o email associado ao token se a sessao for valida e nao expirada.

    Dispara ValueError se token invalido ou expirado.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = (
        db.query(DeviceSession)
        .filter(
            DeviceSession.token == token,
            DeviceSession.logged_in.is_(True),
            DeviceSession.expires_at > now,
        )
        .first()
    )
    if session is None:
        raise ValueError("Token invalido ou expirado.")
    return session.email