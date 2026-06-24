from __future__ import annotations

from fastapi.testclient import TestClient


EMAIL_VALIDO = "teste@exemplo.com"
SENHA_VALIDA = "minha-senha-123"


class TestRegisterEndpoint:
    def test_register_success(self, client: TestClient):
        """Deve cadastrar um novo usuario e retornar token + email."""
        response = client.post(
            "/api/auth/register",
            json={"email": EMAIL_VALIDO, "password": SENHA_VALIDA},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == EMAIL_VALIDO
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0

    def test_register_duplicate_email(self, client: TestClient):
        """Email ja cadastrado deve retornar 409 Conflict."""
        client.post(
            "/api/auth/register",
            json={"email": EMAIL_VALIDO, "password": SENHA_VALIDA},
        )
        response = client.post(
            "/api/auth/register",
            json={"email": EMAIL_VALIDO, "password": "outra-senha"},
        )
        assert response.status_code == 409
        assert "cadastrado" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Email invalido deve retornar 422."""
        response = client.post(
            "/api/auth/register",
            json={"email": "invalido", "password": SENHA_VALIDA},
        )
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """Senha muito curta deve retornar 422."""
        response = client.post(
            "/api/auth/register",
            json={"email": "novo@exemplo.com", "password": "123"},
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    def test_login_success(self, client: TestClient):
        """Login com credenciais corretas deve retornar token."""
        client.post(
            "/api/auth/register",
            json={"email": EMAIL_VALIDO, "password": SENHA_VALIDA},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": EMAIL_VALIDO, "password": SENHA_VALIDA},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == EMAIL_VALIDO
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0

    def test_login_wrong_password(self, client: TestClient):
        """Senha incorreta deve retornar 401."""
        client.post(
            "/api/auth/register",
            json={"email": EMAIL_VALIDO, "password": SENHA_VALIDA},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": EMAIL_VALIDO, "password": "senha-errada"},
        )
        assert response.status_code == 401
        assert "incorretos" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Email nao cadastrado deve retornar 401."""
        response = client.post(
            "/api/auth/login",
            json={"email": "naoexiste@exemplo.com", "password": SENHA_VALIDA},
        )
        assert response.status_code == 401

    def test_login_empty_password(self, client: TestClient):
        """Senha vazia deve retornar 422."""
        response = client.post(
            "/api/auth/login",
            json={"email": EMAIL_VALIDO, "password": ""},
        )
        assert response.status_code == 422


class TestLogoutEndpoint:
    def test_logout_success(self, client: TestClient):
        """Logout com token valido deve invalidar a sessao."""
        reg = client.post(
            "/api/auth/register",
            json={"email": EMAIL_VALIDO, "password": SENHA_VALIDA},
        )
        token = reg.json()["token"]

        response = client.post(
            "/api/auth/logout",
            json={"token": token},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Logout realizado com sucesso."

    def test_logout_invalid_token(self, client: TestClient):
        """Logout com token invalido deve retornar 401."""
        response = client.post(
            "/api/auth/logout",
            json={"token": "token-invalido-123"},
        )
        assert response.status_code == 401

    def test_logout_empty_token(self, client: TestClient):
        """Logout com token vazio deve retornar 422."""
        response = client.post(
            "/api/auth/logout",
            json={"token": ""},
        )
        assert response.status_code == 422

    def test_logout_twice_fails(self, client: TestClient):
        """Segundo logout com mesmo token deve falhar."""
        reg = client.post(
            "/api/auth/register",
            json={"email": EMAIL_VALIDO, "password": SENHA_VALIDA},
        )
        token = reg.json()["token"]

        client.post("/api/auth/logout", json={"token": token})
        response = client.post("/api/auth/logout", json={"token": token})
        assert response.status_code == 401


class TestAuthFlow:
    def test_full_flow_register_login_logout(self, client: TestClient):
        """Fluxo completo: cadastrar, logar com novo token e fazer logout."""
        # Cadastro
        reg = client.post(
            "/api/auth/register",
            json={"email": EMAIL_VALIDO, "password": SENHA_VALIDA},
        )
        assert reg.status_code == 201
        token1 = reg.json()["token"]

        # Login (gera novo token)
        login = client.post(
            "/api/auth/login",
            json={"email": EMAIL_VALIDO, "password": SENHA_VALIDA},
        )
        assert login.status_code == 200
        token2 = login.json()["token"]
        assert token2 != token1  # tokens diferentes

        # Logout do token2
        logout = client.post("/api/auth/logout", json={"token": token2})
        assert logout.status_code == 200

        # token2 nao pode mais ser usado
        logout2 = client.post("/api/auth/logout", json={"token": token2})
        assert logout2.status_code == 401

    def test_password_not_stored_in_plain_text(self, client: TestClient, db_session):
        """Verifica que a senha NUNCA e armazenada como texto puro no banco."""
        from backend.models import User

        client.post(
            "/api/auth/register",
            json={"email": "seguro@exemplo.com", "password": SENHA_VALIDA},
        )
        user = db_session.query(User).filter(User.email == "seguro@exemplo.com").first()
        assert user is not None
        assert user.hashed_password != SENHA_VALIDA
        assert user.hashed_password.startswith("$2b$")  # hash bcrypt