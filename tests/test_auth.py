from __future__ import annotations

from fastapi.testclient import TestClient


class TestAuthSignup:
    def test_signup_success(self, client: TestClient):
        response = client.post(
            "/api/auth/signup",
            json={"email": "alice@test.com", "password": "secret123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Account created successfully"
        assert "token" in data

    def test_signup_duplicate_email(self, client: TestClient):
        client.post(
            "/api/auth/signup",
            json={"email": "bob@test.com", "password": "secret123"},
        )
        response = client.post(
            "/api/auth/signup",
            json={"email": "bob@test.com", "password": "other456"},
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    def test_signup_short_password(self, client: TestClient):
        response = client.post(
            "/api/auth/signup",
            json={"email": "short@test.com", "password": "123"},
        )
        assert response.status_code == 422

    def test_signup_empty_email(self, client: TestClient):
        response = client.post(
            "/api/auth/signup",
            json={"email": "", "password": "123456"},
        )
        assert response.status_code == 422


class TestAuthLogin:
    def test_login_success(self, client: TestClient):
        client.post(
            "/api/auth/signup",
            json={"email": "carol@test.com", "password": "mypassword"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "carol@test.com", "password": "mypassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert "token" in data

    def test_login_wrong_password(self, client: TestClient):
        client.post(
            "/api/auth/signup",
            json={"email": "dave@test.com", "password": "correctpw"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "dave@test.com", "password": "wrongpw"},
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": "whatever"},
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


class TestAuthMe:
    def test_me_authenticated(self, client: TestClient):
        signup_resp = client.post(
            "/api/auth/signup",
            json={"email": "eve@test.com", "password": "pass1234"},
        )
        token = signup_resp.json()["token"]

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "eve@test.com"
        assert "id" in data

    def test_me_no_token(self, client: TestClient):
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    def test_me_invalid_token(self, client: TestClient):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalidtoken123"},
        )
        assert response.status_code == 401


class TestAuthLogout:
    def test_logout_invalidates_session(self, client: TestClient):
        signup_resp = client.post(
            "/api/auth/signup",
            json={"email": "frank@test.com", "password": "pass1234"},
        )
        token = signup_resp.json()["token"]

        # Acessa /me antes do logout
        me_before = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_before.status_code == 200

        # Logout
        logout_resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_resp.status_code == 200
        assert logout_resp.json()["message"] == "Logged out successfully"

        # /me depois do logout deve falhar
        me_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_after.status_code == 401

    def test_logout_no_token(self, client: TestClient):
        response = client.post("/api/auth/logout")
        assert response.status_code == 401


class TestPersistence:
    def test_user_persists_across_requests(self, client: TestClient):
        """Verifica que o usuario criado permanece no banco (teste funcional)."""
        signup_resp = client.post(
            "/api/auth/signup",
            json={"email": "grace@test.com", "password": "persist123"},
        )
        token = signup_resp.json()["token"]

        # Login novamente deve funcionar
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "grace@test.com", "password": "persist123"},
        )
        assert login_resp.status_code == 200
        new_token = login_resp.json()["token"]

        # /me com novo token funciona
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "grace@test.com"
