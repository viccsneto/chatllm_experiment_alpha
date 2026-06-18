from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AuthRegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    token: str
    email: str


class AuthLogoutResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str