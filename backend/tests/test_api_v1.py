"""API v1 tests: success paths, validation errors, missing resources."""

from __future__ import annotations


def _create_company(client, ticker="TSTC", legal_name=None):
    payload = {
        "legal_name": legal_name or f"{ticker} Industries Inc.",
        "display_name": ticker,
        "ticker": ticker,
        "exchange": "NASDAQ",
        "country": "US",
    }
    return client.post("/api/v1/companies", json=payload)


# ── companies ────────────────────────────────────────────────────────────────


def test_create_and_get_company(api_client):
    response = _create_company(api_client)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["ticker"] == "TSTC"
    assert body["display_name"] == "TSTC"

    fetched = api_client.get(f"/api/v1/companies/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["legal_name"] == body["legal_name"]


def test_get_missing_company_404(api_client):
    assert api_client.get("/api/v1/companies/987654").status_code == 404


def test_duplicate_company_conflict_409(api_client):
    first = _create_company(api_client, ticker="DUPL")
    assert first.status_code == 201
    second = _create_company(api_client, ticker="DUPL")
    assert second.status_code == 409


def test_invalid_country_422(api_client):
    response = api_client.post(
        "/api/v1/companies",
        json={"legal_name": "Bad Country Ltd", "country": "USA"},
    )
    assert response.status_code == 422


def test_search_companies(api_client):
    _create_company(api_client, ticker="SRCH", legal_name="Searchable Systems Inc")
    result = api_client.get("/api/v1/companies", params={"q": "searchable"})
    assert result.status_code == 200
    body = result.json()
    assert body["total"] >= 1
    assert any(c["ticker"] == "SRCH" for c in body["items"])


# ── documents ────────────────────────────────────────────────────────────────


def _create_document(client, company_id, **overrides):
    payload = {
        "company_id": company_id,
        "document_type": "10-K",
        "title": "FY2024 Annual Report",
        "fiscal_year": 2024,
        "currency": "USD",
        "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany",
        "source_name": "SEC EDGAR",
        **overrides,
    }
    return client.post("/api/v1/documents", json=payload)


def test_document_lifecycle(api_client):
    company = _create_company(api_client).json()

    created = _create_document(api_client, company["id"])
    assert created.status_code == 201, created.text
    document = created.json()

    listing = api_client.get(f"/api/v1/companies/{company['id']}/documents")
    assert listing.status_code == 200
    assert [d["id"] for d in listing.json()] == [document["id"]]

    fetched = api_client.get(f"/api/v1/documents/{document['id']}")
    assert fetched.status_code == 200

    missing = api_client.get("/api/v1/documents/999999")
    assert missing.status_code == 404


def test_document_for_missing_company_404(api_client):
    response = _create_document(api_client, 555555)
    assert response.status_code == 404


def test_unsupported_document_type_422(api_client):
    company = _create_company(api_client, ticker="BADD").json()
    response = _create_document(api_client, company["id"], document_type="Form 999-X")
    assert response.status_code == 422


def test_invalid_period_dates_422(api_client):
    company = _create_company(api_client, ticker="DATE").json()
    response = _create_document(
        api_client,
        company["id"],
        reporting_period_start="2024-12-31",
        reporting_period_end="2024-01-01",
    )
    assert response.status_code == 422


def test_duplicate_file_hash_409(api_client):
    company = _create_company(api_client, ticker="HASH").json()
    first = _create_document(api_client, company["id"], file_hash="cafe1234")
    assert first.status_code == 201
    second = _create_document(api_client, company["id"], file_hash="cafe1234")
    assert second.status_code == 409


# ── pages / sections / chunks ────────────────────────────────────────────────


def test_pages_flow(api_client):
    company = _create_company(api_client, ticker="PAGS").json()
    document = _create_document(api_client, company["id"]).json()

    page_one = api_client.post(
        f"/api/v1/documents/{document['id']}/pages",
        json={"page_number": 1, "raw_text": "Page one text", "extraction_method": "text"},
    )
    assert page_one.status_code == 201

    duplicate = api_client.post(
        f"/api/v1/documents/{document['id']}/pages",
        json={"page_number": 1, "raw_text": "again"},
    )
    assert duplicate.status_code == 409

    invalid = api_client.post(
        f"/api/v1/documents/{document['id']}/pages",
        json={"page_number": 0, "raw_text": "zero"},
    )
    assert invalid.status_code == 422

    listed = api_client.get(f"/api/v1/documents/{document['id']}/pages")
    assert [p["page_number"] for p in listed.json()] == [1]


def test_sections_hierarchy(api_client):
    company = _create_company(api_client, ticker="SECT").json()
    document = _create_document(api_client, company["id"]).json()

    parent = api_client.post(
        f"/api/v1/documents/{document['id']}/sections",
        json={"section_title": "Risk Factors", "section_type": "Risk Factors",
              "page_start": 5, "page_end": 12},
    )
    assert parent.status_code == 201
    child = api_client.post(
        f"/api/v1/documents/{document['id']}/sections",
        json={"section_title": "Supply Chain Risk", "section_type": "Risk Factors",
              "parent_section_id": parent.json()["id"]},
    )
    assert child.status_code == 201
    assert child.json()["parent_section_id"] == parent.json()["id"]

    bad_parent = api_client.post(
        f"/api/v1/documents/{document['id']}/sections",
        json={"section_title": "Orphan", "section_type": "Other",
              "parent_section_id": 987654},
    )
    assert bad_parent.status_code == 422

    listed = api_client.get(f"/api/v1/documents/{document['id']}/sections")
    assert len(listed.json()) == 2


def test_chunks_flow(api_client):
    company = _create_company(api_client, ticker="CHNK").json()
    document = _create_document(api_client, company["id"]).json()

    chunk = api_client.post(
        f"/api/v1/documents/{document['id']}/chunks",
        json={"chunk_index": 0, "text": "Total revenue grew 8%.", "token_count": 6},
    )
    assert chunk.status_code == 201
    assert chunk.json()["chunk_metadata"] == {}

    dup_index = api_client.post(
        f"/api/v1/documents/{document['id']}/chunks",
        json={"chunk_index": 0, "text": "duplicate index"},
    )
    assert dup_index.status_code == 409

    bad_type = api_client.post(
        f"/api/v1/documents/{document['id']}/chunks",
        json={"chunk_index": 1, "text": "x", "chunk_type": "video"},
    )
    assert bad_type.status_code == 422


# ── financial metrics (provenance) ───────────────────────────────────────────


def test_metrics_flow_with_provenance(api_client):
    company = _create_company(api_client, ticker="MTRX").json()
    document = _create_document(api_client, company["id"]).json()

    chunk = api_client.post(
        f"/api/v1/documents/{document['id']}/chunks",
        json={"chunk_index": 0, "text": "Net sales increased to $391 billion."},
    ).json()

    metric = api_client.post(
        f"/api/v1/companies/{company['id']}/metrics",
        json={
            "document_id": document["id"],
            "metric_name": "Revenue",
            "value": "391035000000.00",
            "unit": "USD",
            "currency": "USD",
            "fiscal_year": 2024,
            "metric_type": "income_statement",
            "source_page": 25,
            "source_chunk_id": chunk["id"],
            "confidence": 0.99,
        },
    )
    assert metric.status_code == 201, metric.text
    body = metric.json()
    assert body["normalized_metric_name"] == "revenue"

    by_name = api_client.get(
        f"/api/v1/companies/{company['id']}/metrics",
        params={"metric_name": "revenue", "fiscal_year": 2024},
    )
    assert [m["id"] for m in by_name.json()] == [body["id"]]

    single = api_client.get(f"/api/v1/companies/{company['id']}/metrics/{body['id']}")
    assert single.status_code == 200

    missing = api_client.get("/api/v1/companies/999999/metrics")
    assert missing.status_code == 404


def test_metric_without_provenance_422(api_client):
    company = _create_company(api_client, ticker="NOPR").json()
    document = _create_document(api_client, company["id"]).json()
    response = api_client.post(
        f"/api/v1/companies/{company['id']}/metrics",
        json={
            "document_id": document["id"],
            "metric_name": "Revenue",
            "value": "100",
        },
    )
    assert response.status_code == 422
    assert "provenance" in response.text.lower()


def test_metric_non_finite_value_422(api_client):
    company = _create_company(api_client, ticker="NANV").json()
    document = _create_document(api_client, company["id"]).json()
    response = api_client.post(
        f"/api/v1/companies/{company['id']}/metrics",
        json={
            "document_id": document["id"],
            "metric_name": "Revenue",
            "value": "NaN",
            "source_page": 1,
        },
    )
    assert response.status_code == 422


def test_metric_cross_company_document_422(api_client):
    company_a = _create_company(api_client, ticker="CMPA").json()
    company_b = _create_company(api_client, ticker="CMPB").json()
    doc_a = _create_document(api_client, company_a["id"]).json()
    response = api_client.post(
        f"/api/v1/companies/{company_b['id']}/metrics",
        json={
            "document_id": doc_a["id"],
            "metric_name": "Revenue",
            "value": "1",
            "source_page": 3,
        },
    )
    assert response.status_code == 422


# ── tables ───────────────────────────────────────────────────────────────────


def test_table_roundtrip_preserves_structure(api_client):
    company = _create_company(api_client, ticker="TBLS").json()
    document = _create_document(api_client, company["id"]).json()

    table_payload = {
        "title": "Revenue by Geography",
        "page_number": 30,
        "headers": ["Region", "2024", "2025"],
        "rows": [
            {"row_index": 0, "row_label": "Americas", "cells": ["Americas", "100B", "110B"]},
            {"row_index": 1, "row_label": "Europe", "cells": ["Europe", "50B", "55B"]},
            {"row_index": 2, "row_label": "Asia", "cells": ["Asia", "30B", "32B"]},
        ],
        "extraction_confidence": 0.95,
    }
    created = api_client.post(
        f"/api/v1/documents/{document['id']}/tables", json=table_payload
    )
    assert created.status_code == 201, created.text
    table = created.json()
    assert len(table["rows"]) == 3
    assert table["headers"] == ["Region", "2024", "2025"]

    fetched = api_client.get(
        f"/api/v1/documents/{document['id']}/tables/{table['id']}"
    )
    rows = fetched.json()["rows"]
    assert [r["row_label"] for r in rows] == ["Americas", "Europe", "Asia"]
    assert rows[1]["cells"] == ["Europe", "50B", "55B"]

    empty_table = api_client.post(
        f"/api/v1/documents/{document['id']}/tables", json={"title": "Empty"}
    )
    assert empty_table.status_code == 422
