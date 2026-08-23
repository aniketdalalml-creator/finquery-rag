"""Company endpoints. Thin HTTP adapters — logic lives in services."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.company import CompanyCreate, CompanyList, CompanyRead, CompanyUpdate
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


def _service(db: Session = Depends(get_db)) -> CompanyService:
    return CompanyService(db)


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, service: CompanyService = Depends(_service)):
    return service.create_company(payload)


@router.get("", response_model=CompanyList)
def list_companies(
    q: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: CompanyService = Depends(_service),
):
    items, total = service.list_companies(query=q, limit=limit, offset=offset)
    return CompanyList(items=items, total=total)


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, service: CompanyService = Depends(_service)):
    return service.get_company(company_id)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    service: CompanyService = Depends(_service),
):
    return service.update_company(company_id, payload)
