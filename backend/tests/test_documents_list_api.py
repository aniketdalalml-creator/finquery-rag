"""Tests for the global documents list endpoint."""

from __future__ import annotations


def test_documents_list_returns_rows_with_company_name(
    api_client, company_factory, document_factory
):
    company = company_factory("LIST", legal_name="Listed Holdings Inc.")
    document_factory(
        company=company,
        title="Annual Report 2024",
        document_type="10-K",
    )
    document_factory(company=None, title="Unassigned Filing")

    response = api_client.get("/api/v1/documents")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list) and len(body) >= 2
    row = next(r for r in body if r["title"] == "Annual Report 2024")
    assert row["company_name"] == "LIST"  # display_name wins over legal_name
    assert row["document_type"] == "10-K"
    assert set(row) == {
        "id",
        "company_id",
        "company_name",
        "title",
        "document_type",
        "filing_date",
        "processing_status",
        "created_at",
    }


def test_documents_list_empty(api_client):
    response = api_client.get("/api/v1/documents")
    assert response.status_code == 200
    assert response.json() == []
