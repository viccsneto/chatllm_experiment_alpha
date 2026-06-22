from __future__ import annotations

from fastapi.testclient import TestClient

from backend.auth_utils import hash_password, verify_password
from backend.models import User


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "minha_senha_secreta"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("senha_correta")
        assert verify_password("senha_errada", hashed) is False


class TestRegisterEndpoint:
    def test_register_success(self, client: TestClient):
        response = client.post(
            "/api/register",
            json={"email": "teste@exemplo.com", "password": "123456"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "teste@exemplo.com"
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client: TestClient):
        client.post("/api/register", json={"email": "dup@exemplo.com", "password": "123456"})
        response = client.post("/api/register", json={"email": "dup@exemplo.com", "password": "123456"})
        assert response.status_code == 409
        assert "ja cadastrado" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        response = client.post("/api/register", json={"email": "invalido", "password": "123456"})
        assert response.status_code == 400
        assert "invalido" in response.json()["detail"].lower()

    def test_register_short_password(self, client: TestClient):
        response = client.post("/api/register", json={"email": "short@exemplo.com", "password": "123"})
        assert response.status_code == 422

    def test_register_empty_fields(self, client: TestClient):
        response = client.post("/api/register", json={"email": "", "password": ""})
        assert response.status_code == 422


class TestLoginEndpoint:
    def test_login_success(self, client: TestClient):
        client.post("/api/register", json={"email": "login@exemplo.com", "password": "123456"})
        response = client.post("/api/login", json={"email": "login@exemplo.com", "password": "123456"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "login@exemplo.com"

    def test_login_wrong_password(self, client: TestClient):
        client.post("/api/register", json={"email": "wrong@exemplo.com", "password": "123456"})
        response = client.post("/api/login", json={"email": "wrong@exemplo.com", "password": "wrongpass"})
        assert response.status_code == 401

    def test_login_nonexistent_email(self, client: TestClient):
        response = client.post("/api/login", json={"email": "naoexiste@exemplo.com", "password": "123456"})
        assert response.status_code == 401


class TestLogoutEndpoint:
    def test_logout_returns_message(self, client: TestClient):
        response = client.post("/api/logout")
        assert response.status_code == 200
        assert "sucesso" in response.json()["message"].lower()


class TestMeEndpoint:
    def test_me_authenticated(self, client: TestClient):
        client.post("/api/register", json={"email": "me@exemplo.com", "password": "123456"})
        login_resp = client.post("/api/login", json={"email": "me@exemplo.com", "password": "123456"})
        token = login_resp.json()["access_token"]

        response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@exemplo.com"
        assert "id" in data

    def test_me_unauthenticated(self, client: TestClient):
        response = client.get("/api/me")
        assert response.status_code == 401


class TestChatEndpointWithAuth:
    """Os endpoints de chat agora exigem autenticacao."""

    def test_chat_without_auth(self, client: TestClient):
        response = client.post("/api/chat", json={"message": "Ola"})
        assert response.status_code == 401

    def test_chat_stream_without_auth(self, client: TestClient):
        response = client.post("/api/chat/stream", json={"message": "Ola"})
        assert response.status_code == 401

    def test_chat_with_auth(self, client: TestClient):
        client.post("/api/register", json={"email": "chatuser@exemplo.com", "password": "123456"})
        login_resp = client.post("/api/login", json={"email": "chatuser@exemplo.com", "password": "123456"})
        token = login_resp.json()["access_token"]

        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Sem OPENROUTER_API_KEY definida, esperamos 503 (config error)
        assert response.status_code in (200, 422, 503)


class TestUserModel:
    def test_create_user(self, db_session):
        user = User(email="model@exemplo.com", hashed_password="hash123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "model@exemplo.com"
        assert user.hashed_password == "hash123"
        assert user.is_active is True

    def test_user_email_unique(self, db_session):
        user1 = User(email="unique@exemplo.com", hashed_password="hash1")
        db_session.add(user1)
        db_session.commit()

        user2 = User(email="unique@exemplo.com", hashed_password="hash2")
        db_session.add(user2)
        import pytest
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            db_session.commit()