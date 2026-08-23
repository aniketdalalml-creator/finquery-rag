"""ingestion pipeline fields

Additive-only migration for the ingestion pipeline (Prompt 3):

- documents: processing_started_at / processing_completed_at / processing_error
- document_pages: extraction_metadata (JSON)
- document_chunks: page_start / page_end (provenance page span)
- financial_tables: units / currency

Revision ID: b3f8c2a91d47
Revises: e2a671f0f512
Create Date: 2026-08-22

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'b3f8c2a91d47'
down_revision: Union[str, None] = 'e2a671f0f512'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('processing_error', sa.Text(), nullable=True))

    with op.batch_alter_table('document_pages', schema=None) as batch_op:
        # Nullable rather than server-defaulted: MySQL rejects literal
        # defaults on JSON columns. The ORM fills {} on insert.
        batch_op.add_column(sa.Column('extraction_metadata', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True))

    with op.batch_alter_table('document_chunks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('page_start', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('page_end', sa.Integer(), nullable=True))

    with op.batch_alter_table('financial_tables', schema=None) as batch_op:
        batch_op.add_column(sa.Column('units', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('currency', sa.String(length=3), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('financial_tables', schema=None) as batch_op:
        batch_op.drop_column('currency')
        batch_op.drop_column('units')

    with op.batch_alter_table('document_chunks', schema=None) as batch_op:
        batch_op.drop_column('page_end')
        batch_op.drop_column('page_start')

    with op.batch_alter_table('document_pages', schema=None) as batch_op:
        batch_op.drop_column('extraction_metadata')

    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_column('processing_error')
        batch_op.drop_column('processing_completed_at')
        batch_op.drop_column('processing_started_at')
