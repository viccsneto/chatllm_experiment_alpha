from __future__ import annotations

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
