"""FinancialMetricRepository — exact, filterable numeric lookups."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.models.metric import FinancialMetric
from app.repositories.base import BaseRepository


class FinancialMetricRepository(BaseRepository[FinancialMetric]):
    model = FinancialMetric

    def list_for_company(
        self,
        company_id: int,
        normalized_metric_name: str | None = None,
        fiscal_year: int | None = None,
        fiscal_quarter: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FinancialMetric]:
        stmt = (
            select(FinancialMetric)
            .where(FinancialMetric.company_id == company_id)
            .order_by(
                FinancialMetric.normalized_metric_name,
                FinancialMetric.period_start.is_(None),
                FinancialMetric.period_start,
                FinancialMetric.fiscal_year.is_(None),
                FinancialMetric.fiscal_year,
            )
        )
        if normalized_metric_name:
            stmt = stmt.where(
                FinancialMetric.normalized_metric_name == normalized_metric_name
            )
        if fiscal_year is not None:
            stmt = stmt.where(FinancialMetric.fiscal_year == fiscal_year)
        if fiscal_quarter:
            stmt = stmt.where(FinancialMetric.fiscal_quarter == fiscal_quarter)
        if period_start is not None:
            stmt = stmt.where(
                (FinancialMetric.period_end >= period_start)
                | (FinancialMetric.period_start >= period_start)
                | FinancialMetric.period_end.is_(None)
            )
        if period_end is not None:
            stmt = stmt.where(
                (FinancialMetric.period_start <= period_end)
                | (FinancialMetric.period_start.is_(None))
            )
        stmt = stmt.limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())
