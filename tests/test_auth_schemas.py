from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
)


class TestRegisterRequest:
    def test_valid(self):
        req = RegisterRequest(email="user@example.com", password="123456")
        assert req.email == "user@example.com"
        assert req.password == "123456"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="invalido", password="123456")

    def test_short_password(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="12345")


class TestRegisterResponse:
    def test_valid(self):
        resp = RegisterResponse(email="a@b.com")
        assert resp.email == "a@b.com"


class TestLoginRequest:
    def test_valid(self):
        req = LoginRequest(email="a@b.com", password="secret", device_fingerprint="fp_abc123")
        assert req.device_fingerprint == "fp_abc123"

    def test_missing_fingerprint(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="a@b.com", password="secret", device_fingerprint="")


class TestLoginResponse:
    def test_valid(self):
        resp = LoginResponse(email="a@b.com", token="uuid-token")
        assert resp.token == "uuid-token"


class TestLogoutRequest:
    def test_valid(self):
        req = LogoutRequest(email="a@b.com", token="some-token")
        assert req.email == "a@b.com"


class TestLogoutResponse:
    def test_valid(self):
        resp = LogoutResponse(message="ok")
        assert resp.message == "ok"


class TestMeResponse:
    def test_valid(self):
        resp = MeResponse(email="a@b.com")
        assert resp.email == "a@b.com"