"""Process + status endpoint flow tests.

The real pipeline's background runner opens its own DB session, so these
tests stub `run_ingestion` and drive terminal statuses through the same
session the API uses — verifying queueing, status reads, error capture
and persistence without touching any other database.
"""

from __future__ import annotations

import pytest

from tests.test_upload_pdf_api import _minimal_pdf, isolated_storage  # noqa: F401


@pytest.fixture
def stubbed_runner(monkeypatch):
    """Replace the background runner with a no-op for endpoint tests."""
    from app.api.v1.routes import documents as documents_route

    monkeypatch.setattr(documents_route, "run_ingestion", lambda *a, **k: None)


def _upload(api_client, company_id: int) -> int:
    response = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("flow.pdf", _minimal_pdf(), "application/pdf")},
        data={"company_id": str(company_id)},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_process_flow_uploaded_to_processed(
    api_client, db_session, company_factory, isolated_storage, stubbed_runner
):
    from app.models.document import Document

    company = company_factory("PRCS")
    document_id = _upload(api_client, company.id)

    before = api_client.get(f"/api/v1/documents/{document_id}/status")
    assert before.status_code == 200
    assert before.json()["status"] == "uploaded"

    queued = api_client.post(f"/api/v1/documents/{document_id}/process")
    assert queued.status_code == 202
    assert api_client.get(f"/api/v1/documents/{document_id}/status").json()[
        "status"
    ] == "queued"

    # Simulate successful processing exactly like the pipeline would.
    row = db_session.get(Document, document_id)
    row.processing_status = "processed"
    row.page_count = 1
    db_session.flush()

    after = api_client.get(f"/api/v1/documents/{document_id}/status")
    body = after.json()
    assert body["status"] == "processed"
    assert body["page_count"] == 1
    assert body["error"] is None


def test_failed_status_carries_error(
    api_client, db_session, company_factory, isolated_storage, stubbed_runner
):
    from app.models.document import Document

    company = company_factory("FAIL")
    document_id = _upload(api_client, company.id)
    api_client.post(f"/api/v1/documents/{document_id}/process")

    row = db_session.get(Document, document_id)
    row.processing_status = "failed"
    row.processing_error = "load produced no pages"
    db_session.flush()

    body = api_client.get(f"/api/v1/documents/{document_id}/status").json()
    assert body["status"] == "failed"
    assert body["error"] == "load produced no pages"


def test_status_persisted_after_terminal(
    api_client, db_session, company_factory, isolated_storage, stubbed_runner
):
    """Status lives in the database, so a fresh read still sees it."""
    from app.models.document import Document

    company = company_factory("PERS")
    document_id = _upload(api_client, company.id)
    api_client.post(f"/api/v1/documents/{document_id}/process")

    db_session.get(Document, document_id).processing_status = "processed"
    db_session.flush()

    db_session.expire_all()  # simulate a brand-new read from the DB
    assert db_session.get(Document, document_id).processing_status == "processed"


def test_process_unknown_document_404(api_client):
    response = api_client.post("/api/v1/documents/999999/process")
    assert response.status_code == 404
