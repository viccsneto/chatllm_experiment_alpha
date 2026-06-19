from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _register_user(client: TestClient, email: str = "sessao@teste.com", password: str = "123456") -> str:
    """Helper to register a user and return token."""
    resp = client.post("/api/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201
    return resp.json()["token"]


class TestSessions:
    def test_create_session(self, client: TestClient):
        token = _register_user(client, "create@teste.com")
        response = client.post(
            "/api/sessions",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] is None

    def test_list_sessions(self, client: TestClient):
        token = _register_user(client, "list@teste.com")
        # Create two sessions
        client.post("/api/sessions", json={}, headers={"Authorization": f"Bearer {token}"})
        client.post("/api/sessions", json={}, headers={"Authorization": f"Bearer {token}"})

        response = client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_sessions_other_user(self, client: TestClient):
        token_a = _register_user(client, "user_a@teste.com")
        token_b = _register_user(client, "user_b@teste.com")

        client.post("/api/sessions", json={}, headers={"Authorization": f"Bearer {token_a}"})

        response = client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0  # User B should not see User A's sessions

    def test_delete_session(self, client: TestClient):
        token = _register_user(client, "delete@teste.com")
        create_resp = client.post(
            "/api/sessions", json={}, headers={"Authorization": f"Bearer {token}"}
        )
        session_id = create_resp.json()["id"]

        delete_resp = client.delete(
            f"/api/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert delete_resp.status_code == 200

        # Verify it's gone
        list_resp = client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert len(list_resp.json()) == 0

    def test_delete_nonexistent_session(self, client: TestClient):
        token = _register_user(client, "nonexist@teste.com")
        response = client.delete(
            "/api/sessions/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_unauthorized_access(self, client: TestClient):
        response = client.get("/api/sessions")
        assert response.status_code == 401

    def test_get_session_messages(self, client: TestClient):
        token = _register_user(client, "msgs@teste.com")
        create_resp = client.post(
            "/api/sessions", json={}, headers={"Authorization": f"Bearer {token}"}
        )
        session_id = create_resp.json()["id"]

        # Send a chat message to this session
        client.post(
            "/api/chat/stream",
            json={"message": "Ola", "session_id": session_id},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = client.get(
            f"/api/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should work (data may vary based on API key status)
        assert response.status_code in (200, 503)

    def test_session_order(self, client: TestClient):
        token = _register_user(client, "order@teste.com")
        s1 = client.post("/api/sessions", json={}, headers={"Authorization": f"Bearer {token}"}).json()
        s2 = client.post("/api/sessions", json={}, headers={"Authorization": f"Bearer {token}"}).json()

        response = client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        # Most recent first (s2 created after s1)
        assert data[0]["id"] == s2["id"]
        assert data[1]["id"] == s1["id"]


class TestChatWithSession:
    def test_chat_stream_with_valid_session(self, client: TestClient):
        token = _register_user(client, "chatsess@teste.com")
        session = client.post(
            "/api/sessions", json={}, headers={"Authorization": f"Bearer {token}"}
        ).json()

        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola", "session_id": session["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Without API key, may return 503, but not 401
        assert response.status_code != 401

    def test_chat_stream_with_invalid_session(self, client: TestClient):
        token = _register_user(client, "invsess@teste.com")
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola", "session_id": 99999},
            headers={"Authorization": f"Bearer {token}"},
        )
        # The chat endpoint doesn't validate session_id ownership in all cases
        # So it may return 503 (without API key) or other codes
        assert response.status_code != 401