"""User request/response schemas. Never include hashed_password."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import StrictModel

_MIN_PASSWORD_LENGTH = 8
_MAX_PASSWORD_LENGTH = 72


class UserRegister(StrictModel):
    email: EmailStr
    password: str = Field(min_length=_MIN_PASSWORD_LENGTH, max_length=_MAX_PASSWORD_LENGTH)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool


class UserLogin(StrictModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=_MAX_PASSWORD_LENGTH)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
