from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestRegister:
    def test_register_success(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "teste@example.com", "password": "123456"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert data["email"] == "teste@example.com"
        assert "user_id" in data

    def test_register_duplicate_email(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": "dupe@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/register",
            json={"email": "dupe@example.com", "password": "123456"},
        )
        assert response.status_code == 409
        assert "ja cadastrado" in response.json()["detail"].lower()

    def test_register_short_email(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "ab", "password": "123456"},
        )
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "short@example.com", "password": "123"},
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": "logintest@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "logintest@example.com", "password": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["email"] == "logintest@example.com"

    def test_login_invalid_password(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": "wrongpw@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "wrongpw@example.com", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "noone@example.com", "password": "123456"},
        )
        assert response.status_code == 401


class TestLogout:
    def test_logout_returns_message(self, client: TestClient):
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Logout realizado com sucesso."


class TestMe:
    def test_me_authenticated(self, client: TestClient):
        reg = client.post(
            "/api/auth/register",
            json={"email": "me@example.com", "password": "123456"},
        )
        token = reg.json()["token"]
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert "id" in data

    def test_me_no_token(self, client: TestClient):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_invalid_token(self, client: TestClient):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalidtoken123"},
        )
        assert response.status_code == 401


class TestChatProtected:
    def test_chat_without_token_returns_401(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
        )
        assert response.status_code == 401

    def test_chat_stream_without_token_returns_401(self, client: TestClient):
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola"},
        )
        assert response.status_code == 401

    def test_chat_with_valid_token(self, client: TestClient):
        reg = client.post(
            "/api/auth/register",
            json={"email": "chat@example.com", "password": "123456"},
        )
        token = reg.json()["token"]
        # Com token valido, esperamos 503 (sem API key) em vez de 401
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code != 401