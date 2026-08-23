"""Tests for the dashboard stats endpoint."""

from __future__ import annotations


def test_dashboard_stats_counts(api_client, db_session, company_factory, document_factory):
    from app.models.metric import FinancialMetric

    company = company_factory("STTS")
    document = document_factory(company=company)
    db_session.add(
        FinancialMetric(
            company_id=company.id,
            document_id=document.id,
            metric_name="Revenue",
            normalized_metric_name="revenue",
            value=123.0,
            unit="units",
        )
    )
    db_session.flush()

    response = api_client.get("/api/v1/stats/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"documents", "companies", "financial_metrics"}
    assert all(isinstance(v, int) for v in body.values())
    assert body["documents"] >= 1
    assert body["companies"] >= 1
    assert body["financial_metrics"] >= 1


def test_dashboard_stats_empty_database(api_client):
    # Rolled-back scratch DB starts empty; endpoint must still answer.
    response = api_client.get("/api/v1/stats/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["documents"] == 0
    assert body["companies"] == 0
    assert body["financial_metrics"] == 0
