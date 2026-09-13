"""Service-layer tests: business rules, normalization, provenance enforcement."""

from __future__ import annotations

import pytest

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.schemas.company import CompanyCreate
from app.schemas.document import DocumentChunkCreate, DocumentCreate, DocumentPageCreate
from app.schemas.metric import FinancialMetricCreate
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.metric_service import FinancialMetricService, normalize_metric_name


def test_normalize_metric_name_variants():
    assert normalize_metric_name("Total Net Sales") == "total_net_sales"
    assert normalize_metric_name("  EBITDA  ") == "ebitda"
    assert normalize_metric_name("Free Cash Flow (FCF)") == "free_cash_flow_fcf"
    assert normalize_metric_name("Debt/EBITDA") == "debt_ebitda"
    assert normalize_metric_name("---") == ""


def test_company_service_duplicate_detection(db_session, company_factory):
    owner_id = company_factory("SEED").user_id
    service = CompanyService(db_session)
    created = service.create_company(
        owner_id,
        CompanyCreate(legal_name="Acme Corp", ticker="ACME", exchange="NYSE"),
    )

    with pytest.raises(ConflictError):
        service.create_company(owner_id, CompanyCreate(legal_name="acme corp"))
    with pytest.raises(ConflictError):
        service.create_company(
            owner_id,
            CompanyCreate(legal_name="Different Name", ticker="acme", exchange="nyse"),
        )
    # Same ticker on a different exchange is allowed.
    other = service.create_company(
        owner_id,
        CompanyCreate(legal_name="Acme Corp Japan", ticker="ACME", exchange="TSE"),
    )
    assert other.id != created.id


def test_company_service_missing_raises(db_session, company_factory):
    owner_id = company_factory("MISS").user_id
    service = CompanyService(db_session)
    with pytest.raises(NotFoundError):
        service.get_company(owner_id, 99999)


def test_document_service_validations(db_session, company_factory):
    service = DocumentService(db_session)
    company = company_factory("DOCS")
    owner_id = company.user_id

    with pytest.raises(NotFoundError):
        service.create_document(
            owner_id,
            DocumentCreate(company_id=424242, document_type="10-K", title="Orphan"),
        )

    document = service.create_document(
        owner_id,
        DocumentCreate(
            company_id=company.id,
            document_type="10-K",
            title="FY2024 10-K",
            file_hash="deadbeef",
        ),
    )
    assert document.user_id == owner_id
    with pytest.raises(ConflictError):
        service.create_document(
            owner_id,
            DocumentCreate(
                company_id=company.id,
                document_type="10-K",
                title="FY2024 10-K copy",
                file_hash="deadbeef",
            ),
        )


def test_document_service_page_and_chunk_rules(db_session, company_factory):
    service = DocumentService(db_session)
    company = company_factory("PGRU")
    owner_id = company.user_id
    document = service.create_document(
        owner_id,
        DocumentCreate(company_id=company.id, document_type="10-Q", title="Q1"),
    )

    page = service.add_page(
        owner_id, document.id, DocumentPageCreate(page_number=1, raw_text="first")
    )
    with pytest.raises(ConflictError):
        service.add_page(
            owner_id, document.id, DocumentPageCreate(page_number=1, raw_text="dup")
        )

    chunk = service.add_chunk(
        owner_id,
        document.id,
        DocumentChunkCreate(chunk_index=0, text="body", chunk_type="text"),
    )
    assert chunk.chunk_metadata == {}

    with pytest.raises(ValidationError):
        service.add_chunk(
            owner_id,
            document.id,
            DocumentChunkCreate(chunk_index=1, text="x", section_id=987654),
        )


def test_metric_service_provenance_enforcement(db_session, company_factory, document_factory):
    metric_service = FinancialMetricService(db_session)
    document_service = DocumentService(db_session)

    company_a = company_factory("AAAA")
    company_b = company_factory("BBBB")
    owner_id = company_a.user_id
    doc_a = document_factory(company=company_a)
    chunk = document_service.add_chunk(
        owner_id, doc_a.id, DocumentChunkCreate(chunk_index=0, text="Revenue $1.0B")
    )

    # Missing provenance pointer entirely → schema-level rejection.
    with pytest.raises(ValueError):
        FinancialMetricCreate(document_id=doc_a.id, metric_name="Revenue", value="1")

    # Chunk from another document → rejected.
    doc_b = document_factory(company=company_b)
    with pytest.raises(ValidationError):
        metric_service.create_metric(
            owner_id,
            company_b.id,
            FinancialMetricCreate(
                document_id=doc_b.id,
                metric_name="Revenue",
                value="2",
                source_chunk_id=chunk.id,
            ),
        )

    # Document of another company → rejected.
    with pytest.raises(ValidationError):
        metric_service.create_metric(
            owner_id,
            company_b.id,
            FinancialMetricCreate(
                document_id=doc_a.id,
                metric_name="Revenue",
                value="3",
                source_page=1,
            ),
        )

    # Valid: normalized name stored for filtering.
    metric = metric_service.create_metric(
        owner_id,
        company_a.id,
        FinancialMetricCreate(
            document_id=doc_a.id,
            metric_name="Gross Profit Margin",
            value="45.5",
            unit="%",
            fiscal_year=2024,
            source_chunk_id=chunk.id,
            confidence="0.97",
        ),
    )
    assert metric.normalized_metric_name == "gross_profit_margin"
    found = metric_service.list_metrics_for_company(
        owner_id, company_a.id, metric_name="gross profit margin"
    )
    assert [m.id for m in found] == [metric.id]
