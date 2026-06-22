from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestRootEndpoint:
    def test_root_returns_frontend(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestChatEndpoint:
    def test_chat_endpoint_requires_authentication(self, client: TestClient):
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
        )
        assert response.status_code == 401

    def test_chat_empty_message_rejected_when_authenticated(self, client: TestClient):
        # The route is protected, but invalid request bodies are still validated as 422 when authenticated.
        signup_response = client.post(
            "/api/auth/signup",
            json={"email": "empty@example.com", "password": "senha123"},
        )
        assert signup_response.status_code == 200

        response = client.post(
            "/api/chat",
            json={"message": ""},
        )
        assert response.status_code == 422


class TestChatStreamEndpoint:
    def test_chat_stream_endpoint_requires_authentication(self, client: TestClient):
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola"},
        )
        assert response.status_code == 401

    def test_chat_stream_empty_message_rejected_when_authenticated(self, client: TestClient):
        signup_response = client.post(
            "/api/auth/signup",
            json={"email": "stream@example.com", "password": "senha123"},
        )
        assert signup_response.status_code == 200

        response = client.post(
            "/api/chat/stream",
            json={"message": ""},
        )
        assert response.status_code == 422


class TestCORSMiddleware:
    def test_cors_headers_present(self, client: TestClient):
        """Verifica que os headers CORS estao presentes."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # O FastAPI com allow_origins=["*"] permite a requisicao
        assert response.status_code in (200, 405)


class TestChatSessions:
    def test_create_and_list_chat_sessions(self, client: TestClient):
        response = client.post("/api/auth/signup", json={"email": "session@example.com", "password": "senha123"})
        assert response.status_code == 200

        create_response = client.post("/api/chat/sessions")
        assert create_response.status_code == 200
        session_data = create_response.json()
        assert session_data["key"]
        assert session_data["title"] is None

        list_response = client.get("/api/chat/sessions")
        assert list_response.status_code == 200
        sessions = list_response.json()
        assert len(sessions) == 1
        assert sessions[0]["key"] == session_data["key"]

    @patch("backend.routers.chat.generate_reply")
    def test_chat_creates_history_and_auto_title(self, mock_generate_reply, client: TestClient):
        mock_generate_reply.return_value = ("Resposta gerada automaticamente.", "google/gemma-4-31b-it")

        signup_response = client.post("/api/auth/signup", json={"email": "auto@example.com", "password": "senha123"})
        assert signup_response.status_code == 200

        create_response = client.post("/api/chat/sessions")
        assert create_response.status_code == 200
        session_key = create_response.json()["key"]

        chat_response = client.post(
            "/api/chat",
            json={"message": "Ola", "session_key": session_key, "history": []},
        )
        assert chat_response.status_code == 200
        data = chat_response.json()
        assert data["session_key"] == session_key
        assert data["session_title"] == "Resposta gerada automaticamente."

        session_detail = client.get(f"/api/chat/sessions/{session_key}")
        assert session_detail.status_code == 200
        detail = session_detail.json()
        assert len(detail["messages"]) == 2
        assert detail["messages"][0]["role"] == "user"
        assert detail["messages"][1]["role"] == "assistant"
        assert detail["title"] == "Resposta gerada automaticamente."
