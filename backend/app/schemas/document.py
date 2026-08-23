"""Document / page / section / chunk request-response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core import constants as C
from app.schemas.common import StrictModel


class DocumentCreate(StrictModel):
    company_id: int | None = None
    document_type: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=512)
    source_url: str | None = Field(default=None, max_length=2048)
    source_name: str | None = Field(default=None, max_length=255)
    filing_date: date | None = None
    reporting_period_start: date | None = None
    reporting_period_end: date | None = None
    fiscal_year: int | None = Field(default=None, ge=1900, le=2100)
    fiscal_quarter: str | None = Field(default=None, pattern=r"^Q[1-4]$")
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    language: str = Field(default="en", min_length=2, max_length=8)
    file_path: str | None = Field(default=None, max_length=1024)
    file_hash: str | None = Field(default=None, max_length=64)
    page_count: int | None = Field(default=None, ge=1)
    processing_status: str = "uploaded"

    @model_validator(mode="after")
    def _check_types(self) -> Self:
        if self.document_type not in C.DOCUMENT_TYPES:
            raise ValueError(
                f"Unsupported document_type {self.document_type!r}. "
                f"Supported: {sorted(C.DOCUMENT_TYPES)}"
            )
        if self.processing_status not in C.PROCESSING_STATUSES:
            raise ValueError(
                f"Unsupported processing_status {self.processing_status!r}. "
                f"Supported: {sorted(C.PROCESSING_STATUSES)}"
            )
        if (
            self.reporting_period_start is not None
            and self.reporting_period_end is not None
            and self.reporting_period_end < self.reporting_period_start
        ):
            raise ValueError("reporting_period_end must be >= reporting_period_start")
        return self


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int | None
    document_type: str
    title: str
    source_url: str | None
    source_name: str | None
    filing_date: date | None
    reporting_period_start: date | None
    reporting_period_end: date | None
    fiscal_year: int | None
    fiscal_quarter: str | None
    currency: str | None
    language: str
    file_path: str | None
    file_hash: str | None
    page_count: int | None
    processing_status: str
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    processing_error: str | None
    created_at: datetime
    updated_at: datetime


class DocumentPageCreate(StrictModel):
    page_number: int = Field(ge=1)
    raw_text: str | None = None
    cleaned_text: str | None = None
    extraction_method: str = "text"
    extraction_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_method(self) -> Self:
        if self.extraction_method not in C.EXTRACTION_METHODS:
            raise ValueError(
                f"Unsupported extraction_method {self.extraction_method!r}. "
                f"Supported: {sorted(C.EXTRACTION_METHODS)}"
            )
        if self.raw_text is None and self.cleaned_text is None:
            raise ValueError("Provide raw_text and/or cleaned_text")
        return self


class DocumentPageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    page_number: int
    raw_text: str | None
    cleaned_text: str | None
    extraction_method: str
    extraction_metadata: dict[str, Any]
    created_at: datetime


class DocumentSectionCreate(StrictModel):
    section_title: str = Field(min_length=1, max_length=512)
    section_type: str = Field(min_length=1, max_length=64)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    text: str | None = None
    parent_section_id: int | None = None

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.section_type not in C.SECTION_TYPES:
            raise ValueError(
                f"Unsupported section_type {self.section_type!r}. "
                f"Supported: {sorted(C.SECTION_TYPES)}"
            )
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError("page_end must be >= page_start")
        return self


class DocumentSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    parent_section_id: int | None
    section_title: str
    section_type: str
    page_start: int | None
    page_end: int | None
    text: str | None
    created_at: datetime


class DocumentChunkCreate(StrictModel):
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1)
    section_id: int | None = None
    chunk_type: str = "text"
    token_count: int | None = Field(default=None, ge=0)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.chunk_type not in C.CHUNK_TYPES:
            raise ValueError(
                f"Unsupported chunk_type {self.chunk_type!r}. "
                f"Supported: {sorted(C.CHUNK_TYPES)}"
            )
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError("page_end must be >= page_start")
        return self


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    section_id: int | None
    chunk_index: int
    chunk_type: str
    text: str
    token_count: int | None
    page_start: int | None
    page_end: int | None
    chunk_metadata: dict[str, Any]
    created_at: datetime
