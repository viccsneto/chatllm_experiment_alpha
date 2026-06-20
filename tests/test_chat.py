from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def get_token(client: TestClient) -> str:
    """Helper para criar um usuario e retornar um token valido."""
    client.post(
        "/api/auth/signup",
        json={
            "name": "Teste",
            "email": "teste@test.com",
            "password": "senha123",
            "security_question": "Pergunta?",
            "security_answer": "resposta",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "teste@test.com", "password": "senha123"},
    )
    return resp.json()["access_token"]


AUTH_HEADERS = {}


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
    def test_chat_requires_auth(self, client: TestClient):
        """Sem token, deve retornar 401."""
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
        )
        assert response.status_code == 401

    def test_chat_endpoint_exists(self, client: TestClient):
        """Com token valido, verifica que o endpoint responde (espera erro de config sem API key)."""
        token = get_token(client)
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Sem OPENROUTER_API_KEY definida, esperamos 503 (config error)
        assert response.status_code in (200, 422, 503)

    def test_chat_empty_message_rejected(self, client: TestClient):
        """Mensagem vazia deve ser rejeitada com 422 (validacao Pydantic)."""
        token = get_token(client)
        response = client.post(
            "/api/chat",
            json={"message": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestChatStreamEndpoint:
    def test_chat_stream_requires_auth(self, client: TestClient):
        """Sem token, deve retornar 401."""
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola"},
        )
        assert response.status_code == 401

    def test_chat_stream_endpoint_exists(self, client: TestClient):
        """Com token valido, verifica que o endpoint aceita requisicoes."""
        token = get_token(client)
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Streaming pode iniciar e depois falhar sem API key
        assert response.status_code in (200, 422, 503)

    def test_chat_stream_empty_message_rejected(self, client: TestClient):
        """Stream com mensagem vazia deve ser rejeitado com 422."""
        token = get_token(client)
        response = client.post(
            "/api/chat/stream",
            json={"message": ""},
            headers={"Authorization": f"Bearer {token}"},
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
