"""add users table

Authentication identity table. Integer primary key and TimestampMixin
columns match the rest of the data layer.

Revision ID: d4e8a1b72c90
Revises: c5d9f2e83a10
Create Date: 2026-09-01

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e8a1b72c90"
down_revision: Union[str, None] = "c5d9f2e83a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    # Expression is double-parenthesized: MySQL functional key parts require
    # it; SQLite/PostgreSQL tolerate the extra level.
    op.create_index(
        "uq_users_email_lower",
        "users",
        [sa.text("(lower(email))")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
