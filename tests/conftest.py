from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth import get_current_user, hash_password
from backend.database import Base, get_db
from backend.main import app
from backend.models import User


@pytest.fixture(scope="session")
def engine():
    """Cria um engine SQLite em memoria para os testes."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def tables(engine):
    """Cria todas as tabelas antes dos testes e as remove ao final."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, tables):
    """Retorna uma sessao de banco limpa para cada teste.

    Usa transacao aninhada (SAVEPOINT) para isolar cada teste.
    Ao final do teste, o rollback desfaz todas as alteracoes.
    """
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
    """Retorna um TestClient do FastAPI com o banco de testes injetado."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Cria um usuario de teste e retorna suas credenciais."""
    user = User(
        email="teste@example.com",
        hashed_password=hash_password("senha123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Faz login e retorna os headers de autorizacao."""
    response = client.post(
        "/api/login",
        json={"email": "teste@example.com", "password": "senha123"},
    )
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_session(db_session, test_user):
    """Cria uma sessao de teste e retorna seu id."""
    from backend.models import Session as ChatSession
    s = ChatSession(user_id=test_user.id)
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s
