"""Extracted financial tables with structure-preserving rows."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.document import JsonType
from app.db.base import Base, BigIntPk, CreatedOnlyMixin


class FinancialTable(Base, CreatedOnlyMixin):
    __tablename__ = "financial_tables"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    page_number: Mapped[int | None] = mapped_column(nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    headers: Mapped[list[Any]] = mapped_column(JsonType, nullable=False, default=list)
    units: Mapped[str | None] = mapped_column(String(32), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    extraction_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 3), nullable=True
    )

    document = relationship("Document", back_populates="tables")
    source_chunk = relationship("DocumentChunk")
    rows: Mapped[list[FinancialTableRow]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="FinancialTableRow.row_index",
    )

    __table_args__ = (
        CheckConstraint(
            "extraction_confidence IS NULL OR (extraction_confidence >= 0"
            " AND extraction_confidence <= 1)",
            name="ck_financial_tables_confidence_range",
        ),
    )


class FinancialTableRow(Base, CreatedOnlyMixin):
    """One table row. `cells` aligns positionally with the parent's headers."""

    __tablename__ = "financial_table_rows"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True)
    table_id: Mapped[int] = mapped_column(
        ForeignKey("financial_tables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_index: Mapped[int] = mapped_column(nullable=False)
    row_label: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cells: Mapped[list[Any]] = mapped_column(JsonType, nullable=False, default=list)

    table = relationship("FinancialTable", back_populates="rows")

    __table_args__ = (
        Index(
            "uq_financial_table_rows_table_index",
            table_id,
            row_index,
            unique=True,
        ),
        CheckConstraint("row_index >= 0", name="ck_financial_table_rows_index_positive"),
    )
