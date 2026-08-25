"""Document family models: documents, pages, sections, chunks."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPk, CreatedOnlyMixin, TimestampMixin

# JSONB on PostgreSQL, plain JSON elsewhere (SQLite dev default).
JsonType = JSON().with_variant(JSONB(), "postgresql")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    document_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reporting_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    reporting_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    fiscal_year: Mapped[int | None] = mapped_column(nullable=True, index=True)
    fiscal_quarter: Mapped[str | None] = mapped_column(String(2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )
    # Ingestion bookkeeping (Prompt 3): never leave a document stuck in
    # `processing` — failures record the error and completion time here.
    processing_started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    processing_completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    company = relationship("Company", lazy="joined")
    pages: Mapped[list[DocumentPage]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )
    sections: Mapped[list[DocumentSection]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )
    tables: Mapped[list["FinancialTable"]] = relationship(  # noqa: F821
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        # Content-level duplicate guard: identical file for the same company.
        Index(
            "uq_documents_company_file_hash",
            company_id,
            file_hash,
            unique=True,
            sqlite_where=text("file_hash IS NOT NULL"),
            postgresql_where=text("file_hash IS NOT NULL"),
        ),
        Index("ix_documents_filing_date", filing_date),
        CheckConstraint(
            "reporting_period_end IS NULL OR reporting_period_start IS NULL"
            " OR reporting_period_end >= reporting_period_start",
            name="ck_documents_period_order",
        ),
    )


class DocumentPage(Base, CreatedOnlyMixin):
    __tablename__ = "document_pages"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(nullable=False, index=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_method: Mapped[str] = mapped_column(
        String(16), nullable=False, default="text"
    )
    # Per-page extraction details (char counts, OCR engine, warnings, ...).
    # Nullable in the DB because MySQL forbids JSON column defaults; the ORM
    # always supplies a dict.
    extraction_metadata: Mapped[dict[str, Any]] = mapped_column(
        "extraction_metadata", JsonType, nullable=True, default=dict
    )

    document = relationship("Document", back_populates="pages")

    __table_args__ = (
        Index(
            "uq_document_pages_doc_page",
            document_id,
            page_number,
            unique=True,
        ),
        CheckConstraint("page_number >= 1", name="ck_document_pages_number_positive"),
    )


class DocumentSection(Base, CreatedOnlyMixin):
    """Hierarchical section: `parent_section_id` enables nesting."""

    __tablename__ = "document_sections"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_section_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_sections.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    section_title: Mapped[str] = mapped_column(String(512), nullable=False)
    section_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    page_start: Mapped[int | None] = mapped_column(nullable=True)
    page_end: Mapped[int | None] = mapped_column(nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    document = relationship("Document", back_populates="sections")
    parent = relationship(
        "DocumentSection", remote_side=[id], backref="children"
    )

    __table_args__ = (
        CheckConstraint(
            "page_end IS NULL OR page_start IS NULL OR page_end >= page_start",
            name="ck_document_sections_page_order",
        ),
    )


class DocumentChunk(Base, CreatedOnlyMixin):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_sections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    chunk_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="text", index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(nullable=True)
    # Page span for provenance (chunk → pages → document).
    page_start: Mapped[int | None] = mapped_column(nullable=True)
    page_end: Mapped[int | None] = mapped_column(nullable=True)
    # Column is `metadata`; attribute differs because Base reserves the name.
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JsonType, nullable=False, default=dict
    )

    # ── Embedding (nullable until the embedding service fills them) ──
    # The vector itself, stored inline; identified by `embedding_id`.
    embedding_vector: Mapped[list[float] | None] = mapped_column(
        JsonType, nullable=True
    )
    embedding_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    embedded_at: Mapped[datetime | None] = mapped_column(nullable=True)

    document = relationship("Document", back_populates="chunks")
    section = relationship("DocumentSection")

    __table_args__ = (
        Index(
            "uq_document_chunks_doc_index",
            document_id,
            chunk_index,
            unique=True,
        ),
        CheckConstraint("chunk_index >= 0", name="ck_document_chunks_index_positive"),
    )
