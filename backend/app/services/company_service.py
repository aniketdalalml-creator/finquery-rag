"""CompanyService — business rules for companies."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.company import Company
from app.repositories.company import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.companies = CompanyRepository(session)

    def create_company(self, payload: CompanyCreate) -> Company:
        legal_name = payload.legal_name.strip()
        ticker = payload.ticker.strip().upper() if payload.ticker else None

        if ticker is not None:
            existing = self.companies.get_by_ticker_and_exchange(
                ticker, payload.exchange
            )
            if existing is not None:
                raise ConflictError(
                    f"Company with ticker {ticker!r} already exists "
                    f"(id={existing.id})"
                )
        existing = self.companies.get_by_legal_name(legal_name)
        if existing is not None:
            raise ConflictError(
                f"Company with legal_name {legal_name!r} already exists "
                f"(id={existing.id})"
            )

        company = Company(
            legal_name=legal_name,
            display_name=(payload.display_name or legal_name).strip(),
            ticker=ticker,
            exchange=payload.exchange,
            country=payload.country.upper() if payload.country else None,
            industry=payload.industry,
            sector=payload.sector,
        )
        return self.companies.add(company)

    def get_company(self, company_id: int) -> Company:
        company = self.companies.get(company_id)
        if company is None:
            raise NotFoundError("Company", company_id)
        return company

    def list_companies(
        self, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Company], int]:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        items = self.companies.search(query=query, limit=limit, offset=offset)
        total = self.companies.count(query=query)
        return items, total

    def update_company(self, company_id: int, payload: CompanyUpdate) -> Company:
        company = self.get_company(company_id)
        data = payload.model_dump(exclude_unset=True)
        if "country" in data and data["country"]:
            data["country"] = data["country"].upper()
        for field, value in data.items():
            setattr(company, field, value)
        self.session.flush()
        return company
