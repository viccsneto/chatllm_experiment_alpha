from __future__ import annotations

from fastapi.testclient import TestClient


def _auth(client: TestClient) -> tuple[str, dict[str, str]]:
    """Register + login e retorna (email, headers)."""
    client.post("/auth/register", json={"email": "sess@test.com", "password": "12345678"})
    resp = client.post("/auth/login", json={
        "email": "sess@test.com",
        "password": "12345678",
        "device_fingerprint": "fp_sess",
    })
    token = resp.json()["token"]
    return "sess@test.com", {"Authorization": f"Bearer {token}"}


class TestSessionCreate:
    def test_create_session(self, client: TestClient):
        email, headers = _auth(client)
        resp = client.post("/api/sessions", json={"user_email": email}, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["title"] is None

    def test_create_unauthorized(self, client: TestClient):
        resp = client.post("/api/sessions", json={"user_email": "a@b.com"})
        assert resp.status_code == 401


class TestSessionList:
    def test_list_empty(self, client: TestClient):
        email, headers = _auth(client)
        resp = client.get(f"/api/sessions?user_email={email}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["sessions"] == []

    def test_list_after_create(self, client: TestClient):
        email, headers = _auth(client)
        client.post("/api/sessions", json={"user_email": email}, headers=headers)
        resp = client.get(f"/api/sessions?user_email={email}", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["sessions"]) == 1


class TestSessionMessages:
    def test_list_messages_empty(self, client: TestClient):
        email, headers = _auth(client)
        resp = client.post("/api/sessions", json={"user_email": email}, headers=headers)
        sid = resp.json()["id"]
        resp = client.get(f"/api/sessions/{sid}/messages?user_email={email}", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_messages_not_found(self, client: TestClient):
        email, headers = _auth(client)
        resp = client.get(f"/api/sessions/nonexistent/messages?user_email={email}", headers=headers)
        assert resp.status_code == 404


class TestSessionDelete:
    def test_delete_session(self, client: TestClient):
        email, headers = _auth(client)
        resp = client.post("/api/sessions", json={"user_email": email}, headers=headers)
        sid = resp.json()["id"]
        resp = client.delete(f"/api/sessions/{sid}?user_email={email}", headers=headers)
        assert resp.status_code == 204

    def test_delete_not_found(self, client: TestClient):
        email, headers = _auth(client)
        resp = client.delete(f"/api/sessions/nonexistent?user_email={email}", headers=headers)
        assert resp.status_code == 404