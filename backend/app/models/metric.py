"""FinancialMetric model.

Deliberately separate from document_chunks: numeric facts need exact,
filterable storage (temporal + per-company queries), not vector search.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPk, CreatedOnlyMixin


class FinancialMetric(Base, CreatedOnlyMixin):
    __tablename__ = "financial_metrics"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Provenance is mandatory at the document level; chunk/page pointers are
    # enforced by the service layer (at least one must be present).
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(30, 10), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    fiscal_year: Mapped[int | None] = mapped_column(nullable=True, index=True)
    fiscal_quarter: Mapped[str | None] = mapped_column(String(2), nullable=True)
    metric_type: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    source_page: Mapped[int | None] = mapped_column(nullable=True)
    source_chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)

    company = relationship("Company")
    document = relationship("Document")
    source_chunk = relationship("DocumentChunk")

    __table_args__ = (
        # Point lookups for "metric X for company Y" and temporal ranges.
        Index(
            "ix_financial_metrics_company_metric_period",
            company_id,
            normalized_metric_name,
            period_start,
            period_end,
        ),
        Index(
            "ix_financial_metrics_company_fiscal",
            company_id,
            fiscal_year,
            fiscal_quarter,
        ),
        CheckConstraint("value = value", name="ck_financial_metrics_value_finite"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_financial_metrics_confidence_range",
        ),
        CheckConstraint(
            "period_end IS NULL OR period_start IS NULL OR period_end >= period_start",
            name="ck_financial_metrics_period_order",
        ),
    )
