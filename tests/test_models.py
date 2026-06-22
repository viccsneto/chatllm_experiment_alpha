from __future__ import annotations

from datetime import datetime, timezone

from backend.models import ChatMessage, Session


class TestChatMessage:
    _counter = 0

    def _make_session(self, db_session):
        from backend.models import User as Usr
        TestChatMessage._counter += 1
        u = Usr(email=f"test_models_{TestChatMessage._counter}@test.com", hashed_password="hash")
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
        s = Session(user_id=u.id)
        db_session.add(s)
        db_session.commit()
        db_session.refresh(s)
        return s

    def test_create_message_defaults(self, db_session):
        """Deve criar uma mensagem com valores padrao para model e created_at."""
        s = self._make_session(db_session)
        msg = ChatMessage(
            session_id=s.id,
            role="user",
            content="Ola, mundo!",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.id is not None
        assert msg.session_id == s.id
        assert msg.role == "user"
        assert msg.content == "Ola, mundo!"
        assert msg.model == "google/gemma-4-31b-it"
        assert isinstance(msg.created_at, datetime)

    def test_create_message_custom_model(self, db_session):
        """Deve criar uma mensagem com modelo customizado."""
        s = self._make_session(db_session)
        msg = ChatMessage(
            session_id=s.id,
            role="user",
            content="Teste",
            model="openai/gpt-4o",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.model == "openai/gpt-4o"

    def test_query_by_session(self, db_session):
        """Deve filtrar mensagens por session_id."""
        s1 = self._make_session(db_session)
        s2 = self._make_session(db_session)
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

    def test_query_by_role(self, db_session):
        """Deve filtrar mensagens pelo campo role."""
        s = self._make_session(db_session)
        msg1 = ChatMessage(session_id=s.id, role="user", content="pergunta")
        msg2 = ChatMessage(session_id=s.id, role="assistant", content="resposta")
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

        assert len(users) == 1
        assert len(assistants) == 1
        assert users[0].content == "pergunta"
        assert assistants[0].content == "resposta"

    def test_created_at_auto_set(self, db_session):
        """O campo created_at deve ser preenchido automaticamente com UTC now."""
        s = self._make_session(db_session)
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        msg = ChatMessage(session_id=s.id, role="user", content="timestamp test")
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)
        after = datetime.now(timezone.utc).replace(tzinfo=None)

        assert before <= msg.created_at <= after

    def test_content_persists_long_text(self, db_session):
        """Deve persistir um texto longo corretamente."""
        s = self._make_session(db_session)
        long_text = "A" * 10000
        msg = ChatMessage(
            session_id=s.id,
            role="user",
            content=long_text,
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert len(msg.content) == 10000
        assert msg.content == long_text

