from __future__ import annotations

from fastapi.testclient import TestClient


class TestAuthRouter:
    def test_register_and_login_flow(self, client: TestClient):
        # Register
        resp = client.post("/auth/register", json={"email": "flow@test.com", "password": "secret123"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "flow@test.com"

        # Register duplicate
        resp = client.post("/auth/register", json={"email": "flow@test.com", "password": "secret123"})
        assert resp.status_code == 409

        # Login
        resp = client.post("/auth/login", json={
            "email": "flow@test.com",
            "password": "secret123",
            "device_fingerprint": "fp_test_device",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "flow@test.com"
        assert "token" in data
        token = data["token"]

        # Me
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "flow@test.com"

        # Logout
        resp = client.post("/auth/logout", json={"email": "flow@test.com", "token": token})
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logout realizado com sucesso."

        # Me apos logout
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_login_wrong_password(self, client: TestClient):
        client.post("/auth/register", json={"email": "wrong@test.com", "password": "correct"})
        resp = client.post("/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrong",
            "device_fingerprint": "fp_test",
        })
        assert resp.status_code == 401

    def test_me_no_token(self, client: TestClient):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client: TestClient):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert resp.status_code == 401