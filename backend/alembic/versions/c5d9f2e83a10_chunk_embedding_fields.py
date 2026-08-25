"""chunk embedding fields

Additive-only migration for chunk embeddings:

- document_chunks: embedding_vector (JSON) / embedding_id / embedding_model
  / embedded_at — all nullable; filled by the embedding service.

Revision ID: c5d9f2e83a10
Revises: b3f8c2a91d47
Create Date: 2026-08-23

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'c5d9f2e83a10'
down_revision: Union[str, None] = 'b3f8c2a91d47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('document_chunks', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'embedding_vector',
                sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column('embedding_id', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('embedding_model', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('embedded_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('document_chunks', schema=None) as batch_op:
        batch_op.drop_column('embedded_at')
        batch_op.drop_column('embedding_model')
        batch_op.drop_column('embedding_id')
        batch_op.drop_column('embedding_vector')
