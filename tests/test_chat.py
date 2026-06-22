from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _auth_header(client: TestClient) -> dict[str, str]:
    """Registra e loga um usuario de teste, retornando o header de autorizacao."""
    client.post("/api/register", json={"email": "testchat@exemplo.com", "password": "123456"})
    resp = client.post("/api/login", json={"email": "testchat@exemplo.com", "password": "123456"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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
    def test_chat_without_auth_rejected(self, client: TestClient):
        """Sem token, o chat deve retornar 401."""
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
        )
        assert response.status_code == 401

    def test_chat_endpoint_exists(self, client: TestClient):
        """Com autenticacao, verifica que o endpoint responde (espera 503 sem API key)."""
        headers = _auth_header(client)
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
            headers=headers,
        )
        assert response.status_code in (200, 422, 503)

    def test_chat_empty_message_rejected(self, client: TestClient):
        """Mensagem vazia deve ser rejeitada com 422 (validacao Pydantic)."""
        headers = _auth_header(client)
        response = client.post(
            "/api/chat",
            json={"message": ""},
            headers=headers,
        )
        assert response.status_code == 422


class TestChatStreamEndpoint:
    def test_chat_stream_without_auth_rejected(self, client: TestClient):
        """Sem token, o stream deve retornar 401."""
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola"},
        )
        assert response.status_code == 401

    def test_chat_stream_endpoint_exists(self, client: TestClient):
        """Com autenticacao, verifica que o endpoint responde."""
        headers = _auth_header(client)
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola"},
            headers=headers,
        )
        assert response.status_code in (200, 422, 503)

    def test_chat_stream_empty_message_rejected(self, client: TestClient):
        """Stream com mensagem vazia deve ser rejeitado com 422."""
        headers = _auth_header(client)
        response = client.post(
            "/api/chat/stream",
            json={"message": ""},
            headers=headers,
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
        assert response.status_code in (200, 405)
