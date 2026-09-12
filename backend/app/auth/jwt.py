"""JWT token service for authenticating users.

Uses ``AUTH_SECRET_KEY`` and ``AUTH_ALGORITHM`` from ``app.auth.config``.
Tokens carry a ``sub`` claim (user id as a string) and ``exp``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt as pyjwt

from app.auth.config import load_auth_config


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    ``sub`` should be a string (user id). Requires ``AUTH_SECRET_KEY``.
    """
    cfg = load_auth_config(require_ready=True)
    to_encode = data.copy()
    delta = expires_delta or timedelta(minutes=cfg.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(UTC) + delta
    to_encode["exp"] = expire
    return pyjwt.encode(to_encode, cfg.AUTH_SECRET_KEY, algorithm=cfg.AUTH_ALGORITHM)


def decode_token(
    token: str, secret_key: str | None = None, algorithm: str | None = None
) -> dict:
    """Decode and validate a JWT payload.

    Raises ``ValueError`` if the token is invalid or expired.
    """
    cfg = load_auth_config(require_ready=True)
    secret = secret_key or cfg.AUTH_SECRET_KEY
    algo = algorithm or cfg.AUTH_ALGORITHM
    try:
        return pyjwt.decode(token, secret, algorithms=[algo])
    except pyjwt.ExpiredSignatureError as exc:
        raise ValueError("Token expired") from exc
    except pyjwt.PyJWTError as exc:
        raise ValueError("Invalid token") from exc
