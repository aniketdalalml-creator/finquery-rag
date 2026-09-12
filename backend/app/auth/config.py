"""Authentication settings (environment-backed).

Importing this module never fails on missing secrets so the rest of the app
and existing tests keep working. Call ``AuthConfig.require_ready()`` when a
later story actually issues tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.auth.exceptions import AuthConfigError
from app.core.config import _env

_DEFAULT_ALGORITHM = "HS256"
_DEFAULT_EXPIRE_MINUTES = "30"
_DEFAULT_BCRYPT_ROUNDS = "12"


def _env_positive_int(name: str, default: str) -> int:
    raw = _env(name, default)
    try:
        value = int(raw)
    except ValueError as exc:
        raise AuthConfigError(f"{name} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise AuthConfigError(f"{name} must be a positive integer, got {value}")
    return value


@dataclass(frozen=True)
class AuthConfig:
    AUTH_SECRET_KEY: str = field(default_factory=lambda: _env("AUTH_SECRET_KEY"))
    AUTH_ALGORITHM: str = field(
        default_factory=lambda: _env("AUTH_ALGORITHM", _DEFAULT_ALGORITHM)
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = field(
        default_factory=lambda: _env_positive_int(
            "ACCESS_TOKEN_EXPIRE_MINUTES", _DEFAULT_EXPIRE_MINUTES
        )
    )
    AUTH_BCRYPT_ROUNDS: int = field(
        default_factory=lambda: _env_positive_int(
            "AUTH_BCRYPT_ROUNDS", _DEFAULT_BCRYPT_ROUNDS
        )
    )

    def require_ready(self) -> None:
        """Fail fast when required settings are missing or blank."""
        if not self.AUTH_SECRET_KEY:
            raise AuthConfigError(
                "AUTH_SECRET_KEY is not set. Add it to the environment "
                "(see .env.example)."
            )
        if not self.AUTH_ALGORITHM:
            raise AuthConfigError("AUTH_ALGORITHM is not set.")
        if not 4 <= self.AUTH_BCRYPT_ROUNDS <= 31:
            raise AuthConfigError(
                "AUTH_BCRYPT_ROUNDS must be between 4 and 31."
            )


def load_auth_config(*, require_ready: bool = False) -> AuthConfig:
    """Build config from the current environment."""
    cfg = AuthConfig()
    if require_ready:
        cfg.require_ready()
    return cfg


auth_config = load_auth_config(require_ready=False)
