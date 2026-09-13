"""Repository tests: CRUD, filtering, company/document relationships."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models.document import DocumentChunk
from app.repositories.company import CompanyRepository
from app.repositories.document import (
    DocumentChunkRepository,
    DocumentPageRepository,
    DocumentRepository,
)
from app.repositories.metric import FinancialMetricRepository


def test_company_repository_crud_and_search(db_session, company_factory):
    owner_id = company_factory("SEED").user_id
    repo = CompanyRepository(db_session)

    created = repo.add(
        CompanyRepository.model(
            user_id=owner_id,
            legal_name="Microsoft Corporation",
            display_name="Microsoft",
            ticker="MSFT",
            exchange="NASDAQ",
        )
    )
    assert created.id is not None

    fetched = repo.get(created.id)
    assert fetched is not None and fetched.ticker == "MSFT"

    by_ticker = repo.get_by_ticker_and_exchange(owner_id, "msft", "nasdaq")
    assert by_ticker is not None and by_ticker.id == created.id

    by_name = repo.get_by_legal_name(owner_id, "microsoft corporation")
    assert by_name is not None and by_name.id == created.id

    hits = repo.search(owner_id, query="micro")
    assert [c.id for c in hits] == [created.id]

    total = repo.count(owner_id, query="micro")
    assert total == 1

    repo.delete(fetched)
    assert repo.get(created.id) is None


def test_document_repository_filtering(db_session, company_factory, document_factory):
    company = company_factory("FLTR")
    owner_id = company.user_id

    doc_10k = document_factory(company=company, document_type="10-K", fiscal_year=2024)
    doc_10q = document_factory(company=company, document_type="10-Q", fiscal_year=2024)

    repo = DocumentRepository(db_session)
    docs = repo.list_by_company(owner_id, company.id)
    assert {d.id for d in docs} == {doc_10k.id, doc_10q.id}

    only_10k = repo.list_by_company(owner_id, company.id, document_type="10-K")
    assert [d.id for d in only_10k] == [doc_10k.id]

    fy2023 = repo.list_by_company(owner_id, company.id, fiscal_year=2023)
    assert fy2023 == []

    duplicate = repo.get_by_file_hash(owner_id, company.id, "ABC123")
    assert duplicate is None
    hashed = document_factory(company=company, file_hash="ABC123")
    found = repo.get_by_file_hash(owner_id, company.id, "abc123")  # case-insensitive
    assert found is not None and found.id == hashed.id


def test_page_and_chunk_repositories_ordering(db_session, document_factory):
    from app.models.document import DocumentPage

    document = document_factory()
    page_repo = DocumentPageRepository(db_session)
    for number in (3, 1, 2):
        page_repo.add(
            DocumentPage(document_id=document.id, page_number=number, raw_text=f"p{number}")
        )
    pages = page_repo.list_for_document(document.id)
    assert [p.page_number for p in pages] == [1, 2, 3]
    assert page_repo.count_for_document(document.id) == 3
    assert page_repo.get_by_number(document.id, 2).raw_text == "p2"

    chunk_repo = DocumentChunkRepository(db_session)
    chunk_repo.add(
        DocumentChunk(
            document_id=document.id,
            chunk_index=1,
            text="second",
            chunk_type="text",
        )
    )
    chunk_repo.add(
        DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            text="first",
            chunk_type="text",
        )
    )
    chunks = chunk_repo.list_for_document(document.id)
    assert [c.chunk_index for c in chunks] == [0, 1]


def test_metric_repository_filters(db_session, company_factory, document_factory):
    from app.models.metric import FinancialMetric

    company = company_factory("MTRC")
    document = document_factory(company=company)
    repo = FinancialMetricRepository(db_session)
    metric = repo.add(
        FinancialMetric(
            company_id=company.id,
            document_id=document.id,
            metric_name="Revenue",
            normalized_metric_name="revenue",
            value=Decimal("100"),
            fiscal_year=2024,
            source_page=1,
        )
    )
    listed = repo.list_for_company(
        company.id, normalized_metric_name="revenue", fiscal_year=2024
    )
    assert [m.id for m in listed] == [metric.id]

    other_company = company_factory("OTHR")
    assert repo.list_for_company(other_company.id) == []
