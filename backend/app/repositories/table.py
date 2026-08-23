"""FinancialTableRepository — structure-preserving table access."""

from __future__ import annotations

from sqlalchemy import select

from app.models.table import FinancialTable, FinancialTableRow
from app.repositories.base import BaseRepository


class FinancialTableRepository(BaseRepository[FinancialTable]):
    model = FinancialTable

    def list_for_document(
        self, document_id: int, limit: int = 100, offset: int = 0
    ) -> list[FinancialTable]:
        stmt = (
            select(FinancialTable)
            .where(FinancialTable.document_id == document_id)
            .order_by(
                FinancialTable.page_number.is_(None),
                FinancialTable.page_number,
                FinancialTable.id,
            )
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt).all())

    def get_with_rows(self, table_id: int) -> FinancialTable | None:
        """Return the table with rows ordered by row_index (reconstructable)."""
        table = self.session.get(FinancialTable, table_id)
        if table is None:
            return None
        stmt = (
            select(FinancialTableRow)
            .where(FinancialTableRow.table_id == table_id)
            .order_by(FinancialTableRow.row_index)
        )
        table.rows = list(self.session.scalars(stmt).all())
        return table

    def add_row(self, row: FinancialTableRow) -> FinancialTableRow:
        self.session.add(row)
        self.session.flush()
        return row
