"""CompanyRepository."""

from __future__ import annotations

from sqlalchemy import func, or_, select

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    model = Company

    def get_for_user(self, company_id: int, user_id: int) -> Company | None:
        stmt = select(Company).where(
            Company.id == company_id,
            Company.user_id == user_id,
        )
        return self._scalar(stmt)

    def get_by_ticker_and_exchange(
        self, user_id: int, ticker: str, exchange: str | None
    ) -> Company | None:
        stmt = select(Company).where(
            Company.user_id == user_id,
            func.lower(Company.ticker) == ticker.lower(),
            (
                func.lower(Company.exchange) == exchange.lower()
                if exchange is not None
                else Company.exchange.is_(None)
            ),
        )
        return self._scalar(stmt)

    def get_by_legal_name(self, user_id: int, legal_name: str) -> Company | None:
        stmt = select(Company).where(
            Company.user_id == user_id,
            func.lower(Company.legal_name) == legal_name.strip().lower(),
        )
        return self._scalar(stmt)

    def search(
        self,
        user_id: int,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Company]:
        stmt = (
            select(Company)
            .where(Company.user_id == user_id)
            .order_by(Company.id)
        )
        if query:
            pattern = f"%{query.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Company.legal_name).like(pattern),
                    func.lower(Company.display_name).like(pattern),
                    func.lower(Company.ticker).like(pattern),
                )
            )
        stmt = stmt.limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())

    def count(self, user_id: int, query: str | None = None) -> int:
        stmt = (
            select(func.count())
            .select_from(Company)
            .where(Company.user_id == user_id)
        )
        if query:
            pattern = f"%{query.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Company.legal_name).like(pattern),
                    func.lower(Company.display_name).like(pattern),
                    func.lower(Company.ticker).like(pattern),
                )
            )
        return int(self.session.scalar(stmt))
