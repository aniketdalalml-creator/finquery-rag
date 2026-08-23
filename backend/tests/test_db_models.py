"""Database-level tests: models, relationships, provenance chain."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.company import Company
from app.models.document import Document, DocumentChunk, DocumentPage, DocumentSection
from app.models.metric import FinancialMetric


def test_company_creation(db_session):
    company = Company(legal_name="Apple Inc.", ticker="AAPL", exchange="NASDAQ")
    db_session.add(company)
    db_session.flush()

    assert company.id is not None
    assert company.created_at is not None
    assert company.updated_at is not None


def test_duplicate_company_ticker_rejected(db_session, company_factory):
    company_factory("DUP", exchange="NASDAQ")
    db_session.add(
        Company(legal_name="Other Corp", ticker="DUP", exchange="NASDAQ")
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_document_creation_and_relationship(db_session, company_factory):
    company = company_factory("REL")
    document = Document(
        company_id=company.id,
        document_type="10-K",
        title="FY2024 Annual Report",
        fiscal_year=2024,
    )
    db_session.add(document)
    db_session.flush()

    assert document.id is not None
    assert document.company.ticker == "REL"
    assert company.documents == [] or all(
        d.company_id == company.id for d in company.documents
    )


def test_document_cascade_deletes_pages(db_session, company_factory, document_factory):
    from sqlalchemy import func, select

    from app.models.document import DocumentPage

    document = document_factory(company=company_factory("CASC"))
    page = DocumentPage(document_id=document.id, page_number=1, raw_text="hello")
    db_session.add(page)
    db_session.flush()

    db_session.delete(document)
    db_session.flush()

    # Bypass the identity map: verify the row is really gone from the DB.
    remaining = db_session.scalar(
        select(func.count())
        .select_from(DocumentPage)
        .where(DocumentPage.document_id == document.id)
    )
    assert remaining == 0


def test_financial_metric_storage_and_provenance_chain(
    db_session, company_factory, document_factory
):
    """metric → chunk → page → document → source_url must be traversable."""
    company = company_factory("PROV")
    document = document_factory(
        company=company,
        title="10-K FY2024",
        source_url="https://www.sec.gov/Archives/edgar/data/demo.htm",
    )
    page = DocumentPage(document_id=document.id, page_number=42, raw_text="Revenue ...")
    section = DocumentSection(
        document_id=document.id,
        section_title="Income Statement",
        section_type="Income Statement",
        page_start=40,
        page_end=45,
    )
    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        chunk_type="financial_metric",
        text="Total net sales were $391,035 million.",
        token_count=9,
    )
    db_session.add_all([page, section, chunk])
    db_session.flush()

    metric = FinancialMetric(
        company_id=company.id,
        document_id=document.id,
        metric_name="Revenue",
        normalized_metric_name="revenue",
        value=Decimal("391035000000"),
        unit="USD",
        currency="USD",
        period_start=date(2023, 9, 25),
        period_end=date(2024, 9, 28),
        fiscal_year=2024,
        metric_type="income_statement",
        source_page=page.page_number,
        source_chunk_id=chunk.id,
        confidence=Decimal("0.99"),
    )
    db_session.add(metric)
    db_session.flush()

    # Walk the full provenance chain.
    assert metric.source_chunk.document_id == document.id
    assert metric.document.source_url.startswith("https://www.sec.gov/")
    pages = (
        db_session.query(DocumentPage)
        .filter_by(document_id=metric.document.id)
        .all()
    )
    assert any(p.page_number == metric.source_page for p in pages)


def test_metric_requires_document_provenance(db_session, company_factory):
    with pytest.raises(IntegrityError):
        db_session.add(
            FinancialMetric(
                company_id=company_factory("NOP").id,
                document_id=None,
                metric_name="Revenue",
                normalized_metric_name="revenue",
                value=Decimal("1"),
            )
        )
        db_session.flush()
