"""User model (authentication identity).

Stores only ``hashed_password`` — never plaintext. Hashing and JWT belong
to later stories; this table is the persistence contract only.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Index, String, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    __table_args__ = (
        # Case-insensitive uniqueness (emails are case-insensitive in practice).
        Index("uq_users_email_lower", text("(lower(email))"), unique=True),
        Index("ix_users_email", "email"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.id} {self.email}>"
