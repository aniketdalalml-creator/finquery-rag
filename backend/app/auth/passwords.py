"""Password hashing (bcrypt). Isolated from routes and the User model.

Callers persist the returned hash on ``User.hashed_password``. This module
never logs the password or includes it in exception messages.
"""

from __future__ import annotations

import bcrypt

from app.auth.config import auth_config
from app.auth.exceptions import InvalidPasswordError

# bcrypt truncates after 72 bytes; reject rather than silently shorten.
_BCRYPT_MAX_BYTES = 72


def _as_password_bytes(password: object) -> bytes:
    if not isinstance(password, str):
        raise InvalidPasswordError("Password must be a string.")
    if password == "":
        raise InvalidPasswordError("Password is required.")
    encoded = password.encode("utf-8")
    if len(encoded) > _BCRYPT_MAX_BYTES:
        raise InvalidPasswordError("Password exceeds the maximum allowed length.")
    return encoded


def hash_password(password: str) -> str:
    """Return a salted bcrypt hash. Never returns the plaintext password."""
    raw = _as_password_bytes(password)
    rounds = auth_config.AUTH_BCRYPT_ROUNDS
    hashed = bcrypt.hashpw(raw, bcrypt.gensalt(rounds=rounds))
    return hashed.decode("ascii")


def verify_password(password: str, hashed_password: str) -> bool:
    """Return True iff ``password`` matches ``hashed_password``.

    Malformed hashes and invalid inputs return False. The password is never
    included in errors.
    """
    if not isinstance(password, str) or not isinstance(hashed_password, str):
        return False
    if password == "" or hashed_password == "":
        return False
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False
