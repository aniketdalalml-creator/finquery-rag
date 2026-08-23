"""Financial metric request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core import constants as C
from app.schemas.common import StrictModel


class FinancialMetricCreate(StrictModel):
    document_id: int  # provenance: metrics must point at a source document
    metric_name: str = Field(min_length=1, max_length=255)
    value: Decimal = Field(allow_inf_nan=False)
    unit: str | None = Field(default=None, max_length=32)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    period_start: date | None = None
    period_end: date | None = None
    fiscal_year: int | None = Field(default=None, ge=1900, le=2100)
    fiscal_quarter: str | None = Field(default=None, pattern=r"^Q[1-4]$")
    metric_type: str | None = None
    source_page: int | None = Field(default=None, ge=1)
    source_chunk_id: int | None = None
    confidence: Decimal | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.metric_type is not None and self.metric_type not in C.METRIC_TYPES:
            raise ValueError(
                f"Unsupported metric_type {self.metric_type!r}. "
                f"Supported: {sorted(C.METRIC_TYPES)}"
            )
        if self.source_chunk_id is None and self.source_page is None:
            raise ValueError(
                "Missing provenance: provide source_chunk_id and/or source_page"
            )
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_end < self.period_start
        ):
            raise ValueError("period_end must be >= period_start")
        return self


class FinancialMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    document_id: int
    metric_name: str
    normalized_metric_name: str
    value: Decimal
    unit: str | None
    currency: str | None
    period_start: date | None
    period_end: date | None
    fiscal_year: int | None
    fiscal_quarter: str | None
    metric_type: str | None
    source_page: int | None
    source_chunk_id: int | None
    confidence: Decimal | None
    created_at: datetime
