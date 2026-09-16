from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse


class TestRegisterSchema:
    def test_valid_register_request(self):
        req = RegisterRequest(email="user@example.com", password="123456")
        assert req.email == "user@example.com"
        assert req.password == "123456"

    def test_invalid_email_format(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="invalido", password="123456")

    def test_short_password(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", password="12345")

    def test_empty_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="", password="123456")


class TestLoginSchema:
    def test_valid_login_request(self):
        req = LoginRequest(email="user@example.com", password="123456")
        assert req.email == "user@example.com"
        assert req.password == "123456"


class TestAuthResponseSchema:
    def test_valid_auth_response(self):
        resp = AuthResponse(access_token="token123", email="user@example.com")
        assert resp.access_token == "token123"
        assert resp.token_type == "bearer"
        assert resp.email == "user@example.com"


class TestUserResponseSchema:
    def test_valid_user_response(self):
        resp = UserResponse(id=1, email="user@example.com", is_active=True)
        assert resp.id == 1
        assert resp.email == "user@example.com"
        assert resp.is_active is True


class TestRegisterEndpoint:
    def test_register_new_user(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "novo@example.com", "password": "123456"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["email"] == "novo@example.com"

    def test_register_duplicate_email(self, client: TestClient):
        # Primeiro registro
        client.post(
            "/api/auth/register",
            json={"email": "duplicado@example.com", "password": "123456"},
        )
        # Segundo registro com mesmo email
        response = client.post(
            "/api/auth/register",
            json={"email": "duplicado@example.com", "password": "123456"},
        )
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data

    def test_register_invalid_email(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "invalido", "password": "123456"},
        )
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "user@example.com", "password": "12345"},
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    def test_login_success(self, client: TestClient):
        # Registrar usuario primeiro
        client.post(
            "/api/auth/register",
            json={"email": "login@example.com", "password": "123456"},
        )
        # Login com credenciais corretas
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "login@example.com"

    def test_login_wrong_password(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": "wrongpw@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "wrongpw@example.com", "password": "senha_errada"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "Credenciais invalidas" in data["detail"]

    def test_login_nonexistent_email(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "naoexiste@example.com", "password": "123456"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "Credenciais invalidas" in data["detail"]


class TestMeEndpoint:
    def test_me_authenticated(self, client: TestClient):
        # Registrar e obter token
        resp = client.post(
            "/api/auth/register",
            json={"email": "me@example.com", "password": "123456"},
        )
        token = resp.json()["access_token"]

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["is_active"] is True
        assert "id" in data

    def test_me_unauthenticated(self, client: TestClient):
        response = client.get("/api/auth/me")
        assert response.status_code == 403

    def test_me_invalid_token(self, client: TestClient):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer token_invalido"},
        )
        assert response.status_code == 401


class TestLogoutEndpoint:
    def test_logout_authenticated(self, client: TestClient):
        resp = client.post(
            "/api/auth/register",
            json={"email": "logout@example.com", "password": "123456"},
        )
        token = resp.json()["access_token"]

        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Logout" in data["message"]

    def test_logout_unauthenticated(self, client: TestClient):
        response = client.post("/api/auth/logout")
        assert response.status_code == 403