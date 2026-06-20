from __future__ import annotations

from fastapi.testclient import TestClient


def get_token(client: TestClient) -> str:
    """Helper para criar um usuario e retornar um token valido."""
    client.post(
        "/api/auth/signup",
        json={
            "name": "Teste",
            "email": "sessao@test.com",
            "password": "senha123",
            "security_question": "Pergunta?",
            "security_answer": "resposta",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "sessao@test.com", "password": "senha123"},
    )
    return resp.json()["access_token"]


def auth_header(client: TestClient) -> dict:
    return {"Authorization": f"Bearer {get_token(client)}"}


class TestListSessions:
    def test_list_sessions_empty(self, client: TestClient):
        response = client.get("/api/sessions", headers=auth_header(client))
        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []

    def test_list_sessions_requires_auth(self, client: TestClient):
        response = client.get("/api/sessions")
        assert response.status_code == 401


class TestCreateSession:
    def test_create_session_success(self, client: TestClient):
        response = client.post(
            "/api/sessions",
            json={},
            headers=auth_header(client),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Nova conversa"
        assert "id" in data

    def test_create_session_custom_title(self, client: TestClient):
        response = client.post(
            "/api/sessions",
            json={"title": "Meu chat"},
            headers=auth_header(client),
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Meu chat"


class TestGetSession:
    def test_get_session_success(self, client: TestClient):
        # Create first
        create_resp = client.post("/api/sessions", json={}, headers=auth_header(client))
        session_id = create_resp.json()["id"]

        response = client.get(f"/api/sessions/{session_id}", headers=auth_header(client))
        assert response.status_code == 200
        assert response.json()["id"] == session_id

    def test_get_session_not_found(self, client: TestClient):
        response = client.get("/api/sessions/99999", headers=auth_header(client))
        assert response.status_code == 404


class TestDeleteSession:
    def test_delete_session_success(self, client: TestClient):
        create_resp = client.post("/api/sessions", json={}, headers=auth_header(client))
        session_id = create_resp.json()["id"]

        response = client.delete(f"/api/sessions/{session_id}", headers=auth_header(client))
        assert response.status_code == 200

        # Verify it's gone
        get_resp = client.get(f"/api/sessions/{session_id}", headers=auth_header(client))
        assert get_resp.status_code == 404


class TestSessionMessages:
    def test_get_messages_empty(self, client: TestClient):
        create_resp = client.post("/api/sessions", json={}, headers=auth_header(client))
        session_id = create_resp.json()["id"]

        response = client.get(
            f"/api/sessions/{session_id}/messages",
            headers=auth_header(client),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == []

    def test_get_messages_requires_auth(self, client: TestClient):
        response = client.get("/api/sessions/1/messages")
        assert response.status_code == 401


class TestGenerateTitle:
    def test_generate_title_from_message(self, client: TestClient):
        # Create session and send a chat message
        create_resp = client.post("/api/sessions", json={}, headers=auth_header(client))
        session_id = create_resp.json()["id"]

        # Chat message will be stored
        token = get_token(client)
        client.post(
            "/api/chat",
            json={"message": "Qual a capital do Brasil?", "session_id": session_id},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = client.post(
            f"/api/sessions/{session_id}/generate-title",
            headers=auth_header(client),
        )
        # May succeed (200) or fail (503 if no API key)
        assert response.status_code in (200, 503)
        if response.status_code == 200:
            assert "title" in response.json()

    def test_generate_title_no_messages(self, client: TestClient):
        create_resp = client.post("/api/sessions", json={}, headers=auth_header(client))
        session_id = create_resp.json()["id"]

        response = client.post(
            f"/api/sessions/{session_id}/generate-title",
            headers=auth_header(client),
        )
        assert response.status_code == 400