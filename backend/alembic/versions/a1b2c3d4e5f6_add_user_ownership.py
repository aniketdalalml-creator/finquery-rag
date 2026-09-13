"""add user ownership to companies and documents

Scopes companies/documents to the authenticated user (per-user library).
Unique constraints move from global to per-user.

Revision ID: a1b2c3d4e5f6
Revises: d4e8a1b72c90
Create Date: 2026-09-13

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "d4e8a1b72c90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("companies") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))

    bind = op.get_bind()
    first_user_id = bind.execute(
        sa.text("SELECT id FROM users ORDER BY id LIMIT 1")
    ).scalar()
    if first_user_id is not None:
        bind.execute(
            sa.text("UPDATE companies SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": first_user_id},
        )
        bind.execute(
            sa.text("UPDATE documents SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": first_user_id},
        )

    bind.execute(sa.text("DELETE FROM documents WHERE user_id IS NULL"))
    bind.execute(sa.text("DELETE FROM companies WHERE user_id IS NULL"))

    # Expression indexes are not reflected by the SQLite dialect — drop manually.
    op.drop_index("uq_companies_legal_name_lower", table_name="companies")
    op.drop_index("ix_companies_display_name_lower", table_name="companies")

    with op.batch_alter_table("companies") as batch_op:
        batch_op.drop_index(
            "uq_companies_ticker_exchange",
            sqlite_where=sa.text("ticker IS NOT NULL"),
            postgresql_where=sa.text("ticker IS NOT NULL"),
        )
        batch_op.alter_column(
            "user_id", existing_type=sa.Integer(), nullable=False
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_companies_user_id_users"),
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index("ix_companies_user_id", ["user_id"], unique=False)
        batch_op.create_index(
            "uq_companies_user_ticker_exchange",
            ["user_id", "ticker", "exchange"],
            unique=True,
            sqlite_where=sa.text("ticker IS NOT NULL"),
            postgresql_where=sa.text("ticker IS NOT NULL"),
        )

    op.create_index(
        "uq_companies_user_legal_name_lower",
        "companies",
        ["user_id", sa.text("(lower(legal_name))")],
        unique=True,
    )
    op.create_index(
        "ix_companies_display_name_lower",
        "companies",
        [sa.text("(lower(display_name))")],
        unique=False,
    )

    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_index(
            "uq_documents_company_file_hash",
            sqlite_where=sa.text("file_hash IS NOT NULL"),
            postgresql_where=sa.text("file_hash IS NOT NULL"),
        )
        batch_op.alter_column(
            "user_id", existing_type=sa.Integer(), nullable=False
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_documents_user_id_users"),
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index("ix_documents_user_id", ["user_id"], unique=False)
        batch_op.create_index(
            "uq_documents_user_company_file_hash",
            ["user_id", "company_id", "file_hash"],
            unique=True,
            sqlite_where=sa.text("file_hash IS NOT NULL"),
            postgresql_where=sa.text("file_hash IS NOT NULL"),
        )


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_index(
            "uq_documents_user_company_file_hash",
            sqlite_where=sa.text("file_hash IS NOT NULL"),
            postgresql_where=sa.text("file_hash IS NOT NULL"),
        )
        batch_op.drop_index("ix_documents_user_id")
        batch_op.drop_constraint(
            batch_op.f("fk_documents_user_id_users"), type_="foreignkey"
        )
        batch_op.drop_column("user_id")
        batch_op.create_index(
            "uq_documents_company_file_hash",
            ["company_id", "file_hash"],
            unique=True,
            sqlite_where=sa.text("file_hash IS NOT NULL"),
            postgresql_where=sa.text("file_hash IS NOT NULL"),
        )

    op.drop_index("uq_companies_user_legal_name_lower", table_name="companies")
    op.drop_index("ix_companies_display_name_lower", table_name="companies")

    with op.batch_alter_table("companies") as batch_op:
        batch_op.drop_index(
            "uq_companies_user_ticker_exchange",
            sqlite_where=sa.text("ticker IS NOT NULL"),
            postgresql_where=sa.text("ticker IS NOT NULL"),
        )
        batch_op.drop_index("ix_companies_user_id")
        batch_op.drop_constraint(
            batch_op.f("fk_companies_user_id_users"), type_="foreignkey"
        )
        batch_op.drop_column("user_id")
        batch_op.create_index(
            "uq_companies_ticker_exchange",
            ["ticker", "exchange"],
            unique=True,
            sqlite_where=sa.text("ticker IS NOT NULL"),
            postgresql_where=sa.text("ticker IS NOT NULL"),
        )

    op.create_index(
        "uq_companies_legal_name_lower",
        "companies",
        [sa.text("(lower(legal_name))")],
        unique=True,
    )
    op.create_index(
        "ix_companies_display_name_lower",
        "companies",
        [sa.text("(lower(display_name))")],
        unique=False,
    )
