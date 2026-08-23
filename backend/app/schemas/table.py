"""Financial table schemas (structure-preserving)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import StrictModel


class TableRowCreate(StrictModel):
    row_index: int = Field(ge=0)
    row_label: str | None = Field(default=None, max_length=512)
    cells: list[Any] = Field(default_factory=list)


class FinancialTableCreate(StrictModel):
    title: str | None = Field(default=None, max_length=512)
    page_number: int | None = Field(default=None, ge=1)
    headers: list[str] = Field(default_factory=list)
    rows: list[TableRowCreate] = Field(default_factory=list)
    units: str | None = Field(default=None, max_length=32)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    source_chunk_id: int | None = None
    extraction_confidence: Decimal | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if not self.headers and not self.rows:
            raise ValueError("Table must define headers and/or rows")
        seen = {row.row_index for row in self.rows}
        if len(seen) != len(self.rows):
            raise ValueError("Duplicate row_index values in table rows")
        return self


class FinancialTableRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    table_id: int
    row_index: int
    row_label: str | None
    cells: list[Any]
    created_at: datetime


class FinancialTableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    source_chunk_id: int | None
    page_number: int | None
    title: str | None
    headers: list[Any]
    units: str | None
    currency: str | None
    extraction_confidence: Decimal | None
    created_at: datetime
    rows: list[FinancialTableRowRead] = []
