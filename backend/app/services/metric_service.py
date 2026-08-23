"""FinancialMetricService — provenance enforcement and normalization."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.models.metric import FinancialMetric
from app.repositories.company import CompanyRepository
from app.repositories.document import (
    DocumentChunkRepository,
    DocumentRepository,
)
from app.repositories.metric import FinancialMetricRepository
from app.schemas.metric import FinancialMetricCreate


def normalize_metric_name(name: str) -> str:
    """Canonical form: lowercase, non-alphanumerics collapsed to underscores."""
    cleaned = name.strip().lower()
    out: list[str] = []
    prev_underscore = False
    for ch in cleaned:
        if ch.isalnum():
            out.append(ch)
            prev_underscore = False
        else:
            if not prev_underscore and out:
                out.append("_")
            prev_underscore = True
    return "".join(out).strip("_")


class FinancialMetricService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.metrics = FinancialMetricRepository(session)
        self.companies = CompanyRepository(session)
        self.documents = DocumentRepository(session)
        self.chunks = DocumentChunkRepository(session)

    def create_metric(
        self, company_id: int, payload: FinancialMetricCreate
    ) -> FinancialMetric:
        self._ensure_company(company_id)
        document = self.documents.get(payload.document_id)
        if document is None:
            raise NotFoundError("Document", payload.document_id)
        # Provenance rule: the metric's document must belong to the same company.
        if document.company_id != company_id:
            raise ValidationError(
                f"Document {payload.document_id} does not belong to "
                f"company {company_id}"
            )
        if payload.source_chunk_id is not None:
            chunk = self.chunks.get(payload.source_chunk_id)
            if chunk is None or chunk.document_id != document.id:
                raise ValidationError(
                    f"source_chunk_id {payload.source_chunk_id} does not belong "
                    f"to document {document.id}"
                )

        metric = FinancialMetric(
            company_id=company_id,
            document_id=payload.document_id,
            metric_name=payload.metric_name.strip(),
            normalized_metric_name=normalize_metric_name(payload.metric_name),
            value=payload.value,
            unit=payload.unit,
            currency=payload.currency,
            period_start=payload.period_start,
            period_end=payload.period_end,
            fiscal_year=payload.fiscal_year,
            fiscal_quarter=payload.fiscal_quarter,
            metric_type=payload.metric_type,
            source_page=payload.source_page,
            source_chunk_id=payload.source_chunk_id,
            confidence=payload.confidence,
        )
        return self.metrics.add(metric)

    def get_metric(self, company_id: int, metric_id: int) -> FinancialMetric:
        self._ensure_company(company_id)
        metric = self.metrics.get(metric_id)
        if metric is None or metric.company_id != company_id:
            raise NotFoundError("FinancialMetric", metric_id)
        return metric

    def list_metrics_for_company(
        self,
        company_id: int,
        metric_name: str | None = None,
        fiscal_year: int | None = None,
        fiscal_quarter: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FinancialMetric]:
        self._ensure_company(company_id)
        normalized = normalize_metric_name(metric_name) if metric_name else None
        return self.metrics.list_for_company(
            company_id,
            normalized_metric_name=normalized,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
            period_start=period_start,
            period_end=period_end,
            limit=max(1, min(limit, 500)),
            offset=max(0, offset),
        )

    def _ensure_company(self, company_id: int) -> None:
        if self.companies.get(company_id) is None:
            raise NotFoundError("Company", company_id)
