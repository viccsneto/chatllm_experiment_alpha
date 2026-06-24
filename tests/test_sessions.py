from __future__ import annotations

import secrets

from fastapi.testclient import TestClient


EMAIL = "sessao@teste.com"
SENHA = "teste123"


def _register_and_login(client: TestClient) -> tuple[str, str]:
    """Cadastra um usuario e retorna (token, email)."""
    client.post(
        "/api/auth/register",
        json={"email": EMAIL, "password": SENHA},
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": EMAIL, "password": SENHA},
    )
    data = resp.json()
    return data["token"], data["email"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestCreateSession:
    def test_create_session_success(self, client: TestClient):
        """Criar sessao retorna 201 com os dados da sessao."""
        token, _ = _register_and_login(client)
        resp = client.post(
            "/api/sessions",
            json={"session_key": "sessao-1"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["session_key"] == "sessao-1"
        assert data["title"] == "Nova conversa"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_session_duplicate(self, client: TestClient):
        """Criar sessao com chave duplicada retorna 409."""
        token, _ = _register_and_login(client)
        client.post(
            "/api/sessions",
            json={"session_key": "sessao-1"},
            headers=_auth_header(token),
        )
        resp = client.post(
            "/api/sessions",
            json={"session_key": "sessao-1"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 409

    def test_create_session_unauthorized(self, client: TestClient):
        """Criar sessao sem token retorna 401 ou 422."""
        resp = client.post(
            "/api/sessions",
            json={"session_key": "sessao-1"},
        )
        assert resp.status_code in (401, 422)

    def test_create_session_invalid_key(self, client: TestClient):
        """Session key vazia retorna 422."""
        token, _ = _register_and_login(client)
        resp = client.post(
            "/api/sessions",
            json={"session_key": ""},
            headers=_auth_header(token),
        )
        assert resp.status_code == 422


class TestListSessions:
    def test_list_sessions_empty(self, client: TestClient):
        """Usuario sem sessoes retorna lista vazia."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/sessions", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["sessions"] == []

    def test_list_sessions_returns_all(self, client: TestClient):
        """Lista retorna todas as sessoes do usuario."""
        token, _ = _register_and_login(client)
        client.post("/api/sessions", json={"session_key": "s1"}, headers=_auth_header(token))
        client.post("/api/sessions", json={"session_key": "s2"}, headers=_auth_header(token))
        resp = client.get("/api/sessions", headers=_auth_header(token))
        assert resp.status_code == 200
        keys = [s["session_key"] for s in resp.json()["sessions"]]
        assert "s1" in keys
        assert "s2" in keys

    def test_list_sessions_ordered_by_updated(self, client: TestClient):
        """Sessoes sao ordenadas pela mais recente."""
        token, _ = _register_and_login(client)
        client.post("/api/sessions", json={"session_key": "a"}, headers=_auth_header(token))
        client.post("/api/sessions", json={"session_key": "b"}, headers=_auth_header(token))
        resp = client.get("/api/sessions", headers=_auth_header(token))
        keys = [s["session_key"] for s in resp.json()["sessions"]]
        assert keys == ["b", "a"]  # b criada depois


class TestUpdateTitle:
    def test_update_title_success(self, client: TestClient):
        """Atualizar titulo retorna 200 com o novo titulo."""
        token, _ = _register_and_login(client)
        client.post("/api/sessions", json={"session_key": "s1"}, headers=_auth_header(token))
        resp = client.patch(
            "/api/sessions/s1/title",
            json={"title": "Meu titulo"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Meu titulo"

    def test_update_title_not_found(self, client: TestClient):
        """Atualizar sessao inexistente retorna 404."""
        token, _ = _register_and_login(client)
        resp = client.patch(
            "/api/sessions/inexistente/title",
            json={"title": "Titulo"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404


class TestDeleteSession:
    def test_delete_session_success(self, client: TestClient):
        """Deletar sessao retorna 200."""
        token, _ = _register_and_login(client)
        client.post("/api/sessions", json={"session_key": "s1"}, headers=_auth_header(token))
        resp = client.delete("/api/sessions/s1", headers=_auth_header(token))
        assert resp.status_code == 200

    def test_delete_session_not_found(self, client: TestClient):
        """Deletar sessao inexistente retorna 404."""
        token, _ = _register_and_login(client)
        resp = client.delete("/api/sessions/inexistente", headers=_auth_header(token))
        assert resp.status_code == 404

    def test_delete_session_removes_messages(self, client: TestClient, db_session):
        """Deletar sessao tambem remove suas mensagens."""
        from backend.models import ChatMessage

        token, _ = _register_and_login(client)
        client.post("/api/sessions", json={"session_key": "s1"}, headers=_auth_header(token))

        # Cria mensagem diretamente no banco
        db_session.add(ChatMessage(session_key="s1", role="user", content="teste"))
        db_session.commit()

        # Deleta a sessao
        client.delete("/api/sessions/s1", headers=_auth_header(token))

        # Verifica que a mensagem foi removida
        msgs = db_session.query(ChatMessage).filter(ChatMessage.session_key == "s1").all()
        assert len(msgs) == 0


class TestGetMessages:
    def test_get_messages_empty(self, client: TestClient):
        """Sessao sem mensagens retorna lista vazia."""
        token, _ = _register_and_login(client)
        client.post("/api/sessions", json={"session_key": "s1"}, headers=_auth_header(token))
        resp = client.get("/api/sessions/s1/messages", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["messages"] == []

    def test_get_messages_returns_all(self, client: TestClient, db_session):
        """Retorna todas as mensagens da sessao ordenadas."""
        from backend.models import ChatMessage

        token, _ = _register_and_login(client)
        client.post("/api/sessions", json={"session_key": "s1"}, headers=_auth_header(token))

        db_session.add(ChatMessage(session_key="s1", role="user", content="pergunta"))
        db_session.add(ChatMessage(session_key="s1", role="assistant", content="resposta"))
        db_session.commit()

        resp = client.get("/api/sessions/s1/messages", headers=_auth_header(token))
        assert resp.status_code == 200
        msgs = resp.json()["messages"]
        assert len(msgs) == 2
        assert msgs[0]["content"] == "pergunta"
        assert msgs[1]["content"] == "resposta"

    def test_get_messages_not_found(self, client: TestClient):
        """Sessao inexistente retorna 404."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/sessions/inexistente/messages", headers=_auth_header(token))
        assert resp.status_code == 404


class TestAuthIsolation:
    def test_sessions_isolated_between_users(self, client: TestClient):
        """Sessoes de um usuario nao aparecem para outro."""
        token1, _ = _register_and_login(client)
        client.post("/api/sessions", json={"session_key": "s1"}, headers=_auth_header(token1))

        # Cadastra segundo usuario
        client.post(
            "/api/auth/register",
            json={"email": "outro@teste.com", "password": SENHA},
        )
        resp2 = client.post(
            "/api/auth/login",
            json={"email": "outro@teste.com", "password": SENHA},
        )
        token2 = resp2.json()["token"]

        resp = client.get("/api/sessions", headers=_auth_header(token2))
        assert resp.json()["sessions"] == []