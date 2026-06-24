from __future__ import annotations

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    token: str
    email: str


class UserResponse(BaseModel):
    id: int
    email: str