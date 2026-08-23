"""Company request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import StrictModel


class CompanyCreate(StrictModel):
    legal_name: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    ticker: str | None = Field(
        default=None, max_length=32, pattern=r"^[A-Za-z0-9.\-]{1,32}$"
    )
    exchange: str | None = Field(default=None, max_length=64)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    industry: str | None = Field(default=None, max_length=128)
    sector: str | None = Field(default=None, max_length=128)


class CompanyUpdate(StrictModel):
    display_name: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    industry: str | None = Field(default=None, max_length=128)
    sector: str | None = Field(default=None, max_length=128)


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    legal_name: str
    display_name: str | None
    ticker: str | None
    exchange: str | None
    country: str | None
    industry: str | None
    sector: str | None
    created_at: datetime
    updated_at: datetime


class CompanyList(BaseModel):
    items: list[CompanyRead]
    total: int
