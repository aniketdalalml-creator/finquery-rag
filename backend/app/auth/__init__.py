"""Authentication package.

Password hashing lives in ``app.auth.passwords``. Registration, login, JWT
issuance, and protected routes belong to later stories.
"""

from app.auth.passwords import hash_password, verify_password

__all__ = ["hash_password", "verify_password"]
