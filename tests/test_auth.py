from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.models import User, UserSession


class TestAuthRoutes:
    def test_signup_creates_user_and_sets_cookie(self, client, db_session):
        response = client.post(
            "/api/auth/signup",
            json={"email": "teste@example.com", "password": "senha123"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Cadastro realizado com sucesso."
        assert response.cookies.get("session_token") is not None

        user = db_session.query(User).filter(User.email == "teste@example.com").one_or_none()
        assert user is not None
        assert user.password_hash != "senha123"

        session = db_session.query(UserSession).filter(UserSession.user_id == user.id).one_or_none()
        assert session is not None

    def test_signup_rejects_duplicate_email(self, client):
        client.post(
            "/api/auth/signup",
            json={"email": "dup@example.com", "password": "senha123"},
        )

        response = client.post(
            "/api/auth/signup",
            json={"email": "dup@example.com", "password": "novaSenha123"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Este email ja esta cadastrado."

    def test_login_with_valid_credentials_sets_cookie(self, client):
        client.post(
            "/api/auth/signup",
            json={"email": "login@example.com", "password": "senha123"},
        )

        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "senha123"},
        )

        assert response.status_code == 200
        assert response.cookies.get("session_token") is not None
        assert response.json()["message"] == "Login realizado com sucesso."

    def test_login_rejects_invalid_credentials(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "naoexiste@example.com", "password": "senha123"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Email ou senha invalidos."

    def test_protected_route_requires_authentication(self, client):
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
        )

        assert response.status_code == 401

    def test_logout_revokes_session(self, client):
        signup_response = client.post(
            "/api/auth/signup",
            json={"email": "logout@example.com", "password": "senha123"},
        )

        assert signup_response.status_code == 200
        token = signup_response.cookies.get("session_token")
        assert token is not None

        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Logout realizado com sucesso."

        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
        )

        assert response.status_code == 401
