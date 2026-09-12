"""Authentication-specific errors.

These are not raised by HTTP routes in this story.
"""

from __future__ import annotations


class AuthError(Exception):
    """Base class for authentication-module errors."""


class AuthConfigError(AuthError):
    """Required auth settings are missing or invalid."""


class AuthNotImplementedError(AuthError, NotImplementedError):
    """Raised by foundation placeholders until a later story implements them."""


class InvalidPasswordError(AuthError):
    """Password input is empty, the wrong type, or otherwise unusable."""
