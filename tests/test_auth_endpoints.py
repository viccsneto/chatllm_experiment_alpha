from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app


@pytest.fixture(scope="module")
def engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="module")
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestAuthRegister:
    def test_register_success(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "teste@email.com", "password": "123456"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "teste@email.com"
        assert data["user"]["is_active"] is True
        assert "id" in data["user"]

    def test_register_duplicate_email(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": "duplicado@email.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/register",
            json={"email": "duplicado@email.com", "password": "123456"},
        )
        assert response.status_code == 409
        assert "ja esta cadastrado" in response.json()["detail"]

    def test_register_invalid_email(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "email-invalido", "password": "123456"},
        )
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "curta@email.com", "password": "123"},
        )
        assert response.status_code == 422


class TestAuthLogin:
    def test_login_success(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": "login@email.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "login@email.com", "password": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "login@email.com"

    def test_login_wrong_password(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": "wrongpw@email.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "wrongpw@email.com", "password": "senha-errada"},
        )
        assert response.status_code == 401
        assert "incorretos" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "naoexiste@email.com", "password": "123456"},
        )
        assert response.status_code == 401


class TestAuthMe:
    def test_me_authenticated(self, client: TestClient):
        resp = client.post(
            "/api/auth/register",
            json={"email": "me@email.com", "password": "123456"},
        )
        token = resp.json()["access_token"]

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@email.com"
        assert data["is_active"] is True

    def test_me_unauthenticated(self, client: TestClient):
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        assert response.json() is None

    def test_me_invalid_token(self, client: TestClient):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer token-invalido"},
        )
        assert response.status_code == 200
        assert response.json() is None


class TestAuthLogout:
    def test_logout(self, client: TestClient):
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Logout realizado com sucesso"