from __future__ import annotations

from backend.models import AuthToken, User
from backend.services.auth import (
    authenticate_user,
    create_token,
    create_user,
    get_user_by_email,
    get_user_by_token,
    hash_password,
    revoke_token,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("minha-senha-segura")
        assert hashed != "minha-senha-segura"
        assert verify_password("minha-senha-segura", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("senha-correta")
        assert verify_password("senha-errada", hashed) is False


class TestCreateUser:
    def test_create_user_success(self, db_session):
        user = create_user(db_session, email="teste@example.com", password="123456")
        assert user.id is not None
        assert user.email == "teste@example.com"
        assert user.is_active is True

    def test_create_user_duplicate_email(self, db_session):
        create_user(db_session, email="dup@example.com", password="123456")
        import pytest
        with pytest.raises(ValueError, match="Email ja cadastrado"):
            create_user(db_session, email="dup@example.com", password="654321")

    def test_password_is_hashed(self, db_session):
        user = create_user(db_session, email="hash@example.com", password="minha-senha")
        assert user.password_hash != "minha-senha"
        assert user.password_hash.startswith("$2b$")


class TestAuthenticateUser:
    def test_authenticate_valid(self, db_session):
        create_user(db_session, email="auth@example.com", password="123456")
        user = authenticate_user(db_session, email="auth@example.com", password="123456")
        assert user is not None
        assert user.email == "auth@example.com"

    def test_authenticate_wrong_password(self, db_session):
        create_user(db_session, email="auth2@example.com", password="123456")
        user = authenticate_user(db_session, email="auth2@example.com", password="wrong")
        assert user is None

    def test_authenticate_unknown_email(self, db_session):
        user = authenticate_user(db_session, email="noone@example.com", password="123456")
        assert user is None


class TestAuthToken:
    def test_create_and_get_token(self, db_session):
        user = create_user(db_session, email="token@example.com", password="123456")
        token = create_token(db_session, user)
        assert token.token is not None
        assert len(token.token) > 20

        found = get_user_by_token(db_session, token.token)
        assert found is not None
        assert found.id == user.id

    def test_revoke_token(self, db_session):
        user = create_user(db_session, email="revoke@example.com", password="123456")
        token = create_token(db_session, user)

        assert get_user_by_token(db_session, token.token) is not None

        revoke_token(db_session, token.token)
        assert get_user_by_token(db_session, token.token) is None

    def test_invalid_token_returns_none(self, db_session):
        assert get_user_by_token(db_session, "token-inexistente") is None

    def test_multiple_tokens_per_user(self, db_session):
        user = create_user(db_session, email="multi@example.com", password="123456")
        token1 = create_token(db_session, user)
        token2 = create_token(db_session, user)

        assert get_user_by_token(db_session, token1.token) is not None
        assert get_user_by_token(db_session, token2.token) is not None


class TestGetUserByEmail:
    def test_find_existing(self, db_session):
        create_user(db_session, email="find@example.com", password="123456")
        user = get_user_by_email(db_session, "find@example.com")
        assert user is not None

    def test_not_found(self, db_session):
        user = get_user_by_email(db_session, "nao.existe@example.com")
        assert user is None