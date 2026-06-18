from __future__ import annotations

from backend.services.auth import create_user


class TestAuthAPI:
    def test_register_success(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "novo@example.com", "password": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["email"] == "novo@example.com"

    def test_register_duplicate_email(self, client, db_session):
        create_user(db_session, email="dup@example.com", password="123456")
        response = client.post(
            "/api/auth/register",
            json={"email": "dup@example.com", "password": "654321"},
        )
        assert response.status_code == 400
        assert "ja cadastrado" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "", "password": "123456"},
        )
        assert response.status_code == 422

    def test_register_short_password(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "short@example.com", "password": "123"},
        )
        assert response.status_code == 422

    def test_login_success(self, client, db_session):
        create_user(db_session, email="login@example.com", password="123456")
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["email"] == "login@example.com"

    def test_login_wrong_password(self, client, db_session):
        create_user(db_session, email="wrongpw@example.com", password="123456")
        response = client.post(
            "/api/auth/login",
            json={"email": "wrongpw@example.com", "password": "wrong"},
        )
        assert response.status_code == 401
        assert "invalido" in response.json()["detail"]

    def test_login_unknown_email(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "noone@example.com", "password": "123456"},
        )
        assert response.status_code == 401

    def test_logout_success(self, client, db_session):
        user = create_user(db_session, email="logout@example.com", password="123456")
        from backend.services.auth import create_token
        token = create_token(db_session, user)
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token.token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Logout realizado com sucesso"

    def test_logout_without_token(self, client):
        response = client.post("/api/auth/logout")
        assert response.status_code == 401

    def test_me_endpoint(self, client, db_session):
        user = create_user(db_session, email="me@example.com", password="123456")
        from backend.services.auth import create_token
        token = create_token(db_session, user)
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token.token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"

    def test_me_invalid_token(self, client):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401