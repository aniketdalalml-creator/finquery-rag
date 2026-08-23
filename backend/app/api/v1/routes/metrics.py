"""Company-scoped financial metric endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.metric import FinancialMetricCreate, FinancialMetricRead
from app.services.metric_service import FinancialMetricService

router = APIRouter(prefix="/companies", tags=["financial-metrics"])


def _service(db: Session = Depends(get_db)) -> FinancialMetricService:
    return FinancialMetricService(db)


@router.post(
    "/{company_id}/metrics",
    response_model=FinancialMetricRead,
    status_code=status.HTTP_201_CREATED,
)
def create_metric(
    company_id: int,
    payload: FinancialMetricCreate,
    service: FinancialMetricService = Depends(_service),
):
    return service.create_metric(company_id, payload)


@router.get("/{company_id}/metrics", response_model=list[FinancialMetricRead])
def list_metrics(
    company_id: int,
    metric_name: str | None = Query(default=None, max_length=255),
    fiscal_year: int | None = Query(default=None, ge=1900, le=2100),
    fiscal_quarter: str | None = Query(default=None, pattern=r"^Q[1-4]$"),
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: FinancialMetricService = Depends(_service),
):
    return service.list_metrics_for_company(
        company_id,
        metric_name=metric_name,
        fiscal_year=fiscal_year,
        fiscal_quarter=fiscal_quarter,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{company_id}/metrics/{metric_id}", response_model=FinancialMetricRead
)
def get_metric(
    company_id: int, metric_id: int, service: FinancialMetricService = Depends(_service)
):
    return service.get_metric(company_id, metric_id)
