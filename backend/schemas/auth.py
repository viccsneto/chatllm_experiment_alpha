from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RegisterResponse(BaseModel):
    email: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    device_fingerprint: str = Field(min_length=1, max_length=512)


class LoginResponse(BaseModel):
    email: str
    token: str


class LogoutRequest(BaseModel):
    email: EmailStr
    token: str = Field(min_length=1, max_length=128)


class LogoutResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    email: str