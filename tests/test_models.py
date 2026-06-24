from __future__ import annotations

from datetime import datetime, timezone

import pytest
from backend.models import ChatMessage, ChatSession, User


@pytest.fixture
def test_user(db_session):
    user = User(email="test@test.com", password_hash="abc")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_session(db_session, test_user):
    sess = ChatSession(user_id=test_user.id)
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)
    return sess


class TestChatMessage:
    def test_create_message_defaults(self, db_session, test_session):
        """Deve criar uma mensagem com valores padrao para model e created_at."""
        msg = ChatMessage(
            session_id=test_session.id,
            role="user",
            content="Ola, mundo!",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.id is not None
        assert msg.session_id == test_session.id
        assert msg.role == "user"
        assert msg.content == "Ola, mundo!"
        assert msg.model == "google/gemma-4-31b-it"
        assert isinstance(msg.created_at, datetime)

    def test_create_message_custom_session(self, db_session, test_user):
        """Deve criar uma mensagem com session_id customizada."""
        s1 = ChatSession(user_id=test_user.id)
        s2 = ChatSession(user_id=test_user.id)
        db_session.add_all([s1, s2])
        db_session.commit()
        db_session.refresh(s1)
        db_session.refresh(s2)

        msg = ChatMessage(
            session_id=s1.id,
            role="assistant",
            content="Resposta do assistente.",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.session_id == s1.id
        assert msg.role == "assistant"

    def test_create_message_custom_model(self, db_session, test_session):
        """Deve criar uma mensagem com modelo customizado."""
        msg = ChatMessage(
            session_id=test_session.id,
            role="user",
            content="Teste",
            model="openai/gpt-4o",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.model == "openai/gpt-4o"

    def test_query_by_session_id(self, db_session, test_user):
        """Deve filtrar mensagens por session_id."""
        s1 = ChatSession(user_id=test_user.id)
        s2 = ChatSession(user_id=test_user.id)
        db_session.add_all([s1, s2])
        db_session.commit()

        msg1 = ChatMessage(session_id=s1.id, role="user", content="a")
        msg2 = ChatMessage(session_id=s2.id, role="user", content="b")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        results = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.session_id == s1.id)
            .all()
        )
        assert len(results) == 1
        assert results[0].content == "a"

    def test_query_by_role(self, db_session, test_session):
        """Deve filtrar mensagens pelo campo role."""
        msg1 = ChatMessage(session_id=test_session.id, role="user", content="pergunta")
        msg2 = ChatMessage(session_id=test_session.id, role="assistant", content="resposta")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        users = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.role == "user")
            .all()
        )
        assistants = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.role == "assistant")
            .all()
        )

        assert len(users) >= 1
        assert any(m.content == "pergunta" for m in users)
        assert len(assistants) >= 1
        assert any(m.content == "resposta" for m in assistants)

    def test_created_at_auto_set(self, db_session, test_session):
        """Deve definir created_at automaticamente ao criar uma mensagem."""
        msg = ChatMessage(
            session_id=test_session.id,
            role="user",
            content="Teste de timestamp",
        )
        db_session.add(msg)
        db_session.commit()

        assert msg.created_at is not None
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        diff = abs((now - msg.created_at).total_seconds())
        assert diff < 5, "created_at deve ser proximo ao horario atual"

    def test_content_persists_long_text(self, db_session, test_session):
        """Deve persistir corretamente um texto longo."""
        long_content = "A" * 5000
        msg = ChatMessage(
            session_id=test_session.id,
            role="user",
            content=long_content,
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.content == long_content
        assert len(msg.content) == 5000
