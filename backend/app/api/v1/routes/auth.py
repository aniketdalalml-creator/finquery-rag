"""Auth HTTP adapters. Business logic lives in AuthService."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import LoginResponse, UserRead, UserLogin, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, service: AuthService = Depends(_service)):
    return service.register(payload)


@router.post("/login", response_model=LoginResponse)
def login(payload: UserLogin, service: AuthService = Depends(_service)):
    user, token = service.login(payload)
    return LoginResponse(access_token=token, token_type="bearer", user=user)
