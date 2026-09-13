"""Dashboard statistics endpoints (read-only counters)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import Company
from app.models.document import Document
from app.models.metric import FinancialMetric
from app.models.user import User
from app.security import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


class DashboardStatsResponse(BaseModel):
    documents: int
    companies: int
    financial_metrics: int


@router.get("/dashboard", response_model=DashboardStatsResponse)
def dashboard_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DashboardStatsResponse:
    return DashboardStatsResponse(
        documents=db.query(Document).filter(Document.user_id == user.id).count(),
        companies=db.query(Company).filter(Company.user_id == user.id).count(),
        financial_metrics=(
            db.query(FinancialMetric)
            .join(Company, FinancialMetric.company_id == Company.id)
            .filter(Company.user_id == user.id)
            .count()
        ),
    )
