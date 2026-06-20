from __future__ import annotations

from fastapi.testclient import TestClient


class TestSignup:
    def test_signup_success(self, client: TestClient):
        response = client.post(
            "/api/auth/signup",
            json={
                "name": "Alice",
                "email": "alice@test.com",
                "password": "secret123",
                "security_question": "Qual seu animal favorito?",
                "security_answer": "gato",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "alice@test.com"
        assert data["user"]["name"] == "Alice"
        assert "id" in data["user"]

    def test_signup_duplicate_email(self, client: TestClient):
        payload = {
            "name": "Bob",
            "email": "bob@test.com",
            "password": "secret123",
            "security_question": "Pergunta?",
            "security_answer": "resposta",
        }
        # Primeiro cadastro
        client.post("/api/auth/signup", json=payload)
        # Segundo cadastro com mesmo email
        response = client.post("/api/auth/signup", json=payload)
        assert response.status_code == 409
        assert "ja esta cadastrado" in response.json()["detail"].lower()

    def test_signup_invalid_data(self, client: TestClient):
        response = client.post(
            "/api/auth/signup",
            json={
                "name": "",
                "email": "invalido",
                "password": "12",
                "security_question": "",
                "security_answer": "",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient):
        # Primeiro cadastra
        client.post(
            "/api/auth/signup",
            json={
                "name": "Carlos",
                "email": "carlos@test.com",
                "password": "minhasenha",
                "security_question": "Cor favorita?",
                "security_answer": "azul",
            },
        )
        # Depois faz login
        response = client.post(
            "/api/auth/login",
            json={"email": "carlos@test.com", "password": "minhasenha"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "carlos@test.com"

    def test_login_wrong_password(self, client: TestClient):
        client.post(
            "/api/auth/signup",
            json={
                "name": "Diana",
                "email": "diana@test.com",
                "password": "senhacerta",
                "security_question": "Pergunta?",
                "security_answer": "resposta",
            },
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "diana@test.com", "password": "senhaerrada"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_email(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "noone@test.com", "password": "qualquer"},
        )
        assert response.status_code == 401


class TestForgotPassword:
    def test_forgot_password_flow(self, client: TestClient):
        # Cadastra usuario
        client.post(
            "/api/auth/signup",
            json={
                "name": "Eva",
                "email": "eva@test.com",
                "password": "senha123",
                "security_question": "Cidade natal?",
                "security_answer": "recife",
            },
        )
        # Solicita recuperacao
        resp1 = client.post(
            "/api/auth/forgot-password", json={"email": "eva@test.com"}
        )
        assert resp1.status_code == 200
        assert resp1.json()["security_question"] == "Cidade natal?"

        # Verifica resposta de seguranca
        resp2 = client.post(
            "/api/auth/verify-security-answer",
            json={"email": "eva@test.com", "security_answer": "recife"},
        )
        assert resp2.status_code == 200

        # Resposta errada
        resp3 = client.post(
            "/api/auth/verify-security-answer",
            json={"email": "eva@test.com", "security_answer": "errada"},
        )
        assert resp3.status_code == 401

        # Redefine senha
        resp4 = client.post(
            "/api/auth/reset-password",
            json={"email": "eva@test.com", "new_password": "novaSenha456"},
        )
        assert resp4.status_code == 200

        # Testa login com nova senha
        resp5 = client.post(
            "/api/auth/login",
            json={"email": "eva@test.com", "password": "novaSenha456"},
        )
        assert resp5.status_code == 200

    def test_forgot_password_nonexistent(self, client: TestClient):
        response = client.post(
            "/api/auth/forgot-password", json={"email": "fake@test.com"}
        )
        assert response.status_code == 404


class TestLogout:
    def test_logout(self, client: TestClient):
        response = client.post("/api/auth/logout", json={})
        assert response.status_code == 200
        assert "sucesso" in response.json()["message"].lower()


class TestAuthMe:
    def test_get_me_authenticated(self, client: TestClient):
        # Cadastra e faz login
        client.post(
            "/api/auth/signup",
            json={
                "name": "Felipe",
                "email": "felipe@test.com",
                "password": "senha123",
                "security_question": "Pergunta?",
                "security_answer": "resposta",
            },
        )
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "felipe@test.com", "password": "senha123"},
        )
        token = login_resp.json()["access_token"]

        # Acessa /api/auth/me
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "felipe@test.com"
        assert data["name"] == "Felipe"

    def test_get_me_unauthenticated(self, client: TestClient):
        response = client.get("/api/auth/me")
        assert response.status_code == 401