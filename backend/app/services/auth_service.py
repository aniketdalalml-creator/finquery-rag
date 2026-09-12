"""Authentication application service. Routes stay thin."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.exceptions import AuthConfigError, InvalidPasswordError
from app.auth.jwt import create_access_token
from app.auth.passwords import hash_password, verify_password
from app.core.errors import AuthenticationError, ConflictError, ValidationError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserLogin, UserRegister

_GENERIC_LOGIN_ERROR = "Invalid email or password."


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def register(self, payload: UserRegister) -> User:
        email = str(payload.email).strip().lower()
        existing = self.users.get_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists.")

        try:
            hashed = hash_password(payload.password)
        except InvalidPasswordError as exc:
            raise ValidationError(str(exc)) from exc

        user = User(email=email, hashed_password=hashed, is_active=True)
        try:
            return self.users.add(user)
        except IntegrityError as exc:
            raise ConflictError("An account with this email already exists.") from exc

    def login(self, payload: UserLogin) -> tuple[User, str]:
        email = str(payload.email).strip().lower()
        user = self.users.get_by_email(email)
        password_ok = False
        if user is not None:
            password_ok = verify_password(payload.password, user.hashed_password)

        if user is None or not password_ok or not user.is_active:
            raise AuthenticationError(_GENERIC_LOGIN_ERROR)

        try:
            token = create_access_token({"sub": str(user.id)})
        except AuthConfigError as exc:
            raise ValidationError(
                "Authentication is not configured. Set AUTH_SECRET_KEY."
            ) from exc
        return user, token
