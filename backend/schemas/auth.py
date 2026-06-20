from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    security_question: str = Field(min_length=1, max_length=255)
    security_answer: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)


class VerifySecurityAnswerRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    security_answer: str = Field(min_length=1, max_length=255)


class ResetPasswordRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=6, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class SecurityQuestionResponse(BaseModel):
    security_question: str


class MessageResponse(BaseModel):
    message: str