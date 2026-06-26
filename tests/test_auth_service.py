from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.models import DeviceSession, HashingKey, User
from backend.services.auth import (
    _ensure_active_key,
    _compute_hash,
    _time_safe_equal,
    _verify_hash,
    get_logged_in_email,
    login_user,
    logout_user,
    register_user,
)


class TestEnsureActiveKey:
    def test_creates_key_when_none_exists(self, db_session: Session):
        key = _ensure_active_key(db_session)
        assert key is not None
        assert key.active is True
        assert len(key.key_id) == 12

    def test_reuses_existing_active_key(self, db_session: Session):
        key1 = _ensure_active_key(db_session)
        key2 = _ensure_active_key(db_session)
        assert key1.id == key2.id


class TestComputeHash:
    def test_deterministic(self):
        h1 = _compute_hash("secret", "a@b.com", "mypass")
        h2 = _compute_hash("secret", "a@b.com", "mypass")
        assert h1 == h2

    def test_different_email_gives_different_hash(self):
        h1 = _compute_hash("secret", "a@b.com", "mypass")
        h2 = _compute_hash("secret", "b@b.com", "mypass")
        assert h1 != h2

    def test_different_password_gives_different_hash(self):
        h1 = _compute_hash("secret", "a@b.com", "pass1")
        h2 = _compute_hash("secret", "a@b.com", "pass2")
        assert h1 != h2


class TestTimeSafeEqual:
    def test_equal_strings(self):
        assert _time_safe_equal("abc", "abc") is True

    def test_different_strings(self):
        assert _time_safe_equal("abc", "xyz") is False

    def test_different_lengths(self):
        assert _time_safe_equal("abc", "abcd") is False


class TestVerifyHash:
    def test_valid_hash(self, db_session: Session):
        key = _ensure_active_key(db_session)
        h = _compute_hash(key.key_value, "a@b.com", "pass")
        stored = f"{key.key_id}:{h}"
        assert _verify_hash(stored, "a@b.com", "pass", db_session) is True

    def test_wrong_password(self, db_session: Session):
        key = _ensure_active_key(db_session)
        h = _compute_hash(key.key_value, "a@b.com", "pass")
        stored = f"{key.key_id}:{h}"
        assert _verify_hash(stored, "a@b.com", "wrong", db_session) is False

    def test_wrong_email(self, db_session: Session):
        key = _ensure_active_key(db_session)
        h = _compute_hash(key.key_value, "a@b.com", "pass")
        stored = f"{key.key_id}:{h}"
        assert _verify_hash(stored, "b@b.com", "pass", db_session) is False

    def test_invalid_format(self, db_session: Session):
        assert _verify_hash("invalid-hash", "a@b.com", "pass", db_session) is False

    def test_nonexistent_key_id(self, db_session: Session):
        stored = "nonexistent:abc123"
        assert _verify_hash(stored, "a@b.com", "pass", db_session) is False


class TestRegisterUser:
    def test_register_success(self, db_session: Session):
        user = register_user(db_session, "new@test.com", "secret123")
        assert user.email == "new@test.com"
        assert ":" in user.password_hash

    def test_register_duplicate_email(self, db_session: Session):
        register_user(db_session, "dup@test.com", "secret123")
        with pytest.raises(ValueError, match="Email ja cadastrado"):
            register_user(db_session, "dup@test.com", "otherpass")


class TestLoginUser:
    def test_login_success(self, db_session: Session):
        register_user(db_session, "login@test.com", "mypass")
        token = login_user(db_session, "login@test.com", "mypass", "fp_device1")
        assert isinstance(token, str) and len(token) > 0

    def test_login_wrong_password(self, db_session: Session):
        register_user(db_session, "wrong@test.com", "correct")
        with pytest.raises(ValueError, match="Email ou senha incorretos"):
            login_user(db_session, "wrong@test.com", "wrong", "fp_device1")

    def test_login_nonexistent_user(self, db_session: Session):
        with pytest.raises(ValueError, match="Email ou senha incorretos"):
            login_user(db_session, "nobody@test.com", "pass", "fp_device1")


class TestLogoutUser:
    def test_logout_success(self, db_session: Session):
        register_user(db_session, "out@test.com", "pass")
        token = login_user(db_session, "out@test.com", "pass", "fp_device1")
        logout_user(db_session, "out@test.com", token)
        # Apos logout, o token nao deve ser valido
        with pytest.raises(ValueError, match="Token invalido ou expirado"):
            get_logged_in_email(db_session, token)

    def test_logout_invalid_token(self, db_session: Session):
        with pytest.raises(ValueError, match="Sessao nao encontrada"):
            logout_user(db_session, "any@test.com", "fake-token")


class TestGetLoggedInEmail:
    def test_valid_token(self, db_session: Session):
        register_user(db_session, "me@test.com", "pass")
        token = login_user(db_session, "me@test.com", "pass", "fp_device1")
        email = get_logged_in_email(db_session, token)
        assert email == "me@test.com"

    def test_expired_token(self, db_session: Session):
        from datetime import timedelta, timezone, datetime
        from backend.models import DeviceSession

        register_user(db_session, "exp@test.com", "pass")
        token = login_user(db_session, "exp@test.com", "pass", "fp_device1")

        # Forcar expiracao
        session = db_session.query(DeviceSession).filter(DeviceSession.token == token).first()
        session.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        db_session.commit()

        with pytest.raises(ValueError, match="Token invalido ou expirado"):
            get_logged_in_email(db_session, token)