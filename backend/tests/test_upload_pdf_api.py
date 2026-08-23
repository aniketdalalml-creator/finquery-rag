"""End-to-end tests for the document upload API endpoint.

Covers: valid PDF accepted, invalid files rejected, duplicate content
deduplicated, and the record persisted in the scratch database.
Storage is redirected to a temp dir so the real storage_data folder
(and the production MySQL database) is never touched.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """Point LocalStorageBackend at a temp dir for this test."""
    from app.core import config as config_module
    from app.storage import get_storage

    monkeypatch.setattr(
        config_module.config, "STORAGE_PATH", str(tmp_path / "storage")
    )
    # Drop cached backend instances so the new path takes effect.
    import app.storage as storage_pkg

    if hasattr(storage_pkg, "_instances"):
        storage_pkg._instances.clear()
    yield get_storage()
    if hasattr(storage_pkg, "_instances"):
        storage_pkg._instances.clear()


def _minimal_pdf() -> bytes:
    """A one-page PDF pypdf can parse, built with correct xref offsets."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF"
    ).encode()
    return bytes(out)


def test_valid_pdf_uploads(api_client, db_session, company_factory, isolated_storage):
    company = company_factory("PDFCO")
    response = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("report.pdf", _minimal_pdf(), "application/pdf")},
        data={"company_id": str(company.id), "document_type": "10-K"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["title"] == "report.pdf"
    assert body["processing_status"] == "uploaded"
    assert body["company_id"] == company.id

    # Record actually persisted in this session's database.
    from app.models.document import Document

    assert db_session.get(Document, body["id"]) is not None


def test_invalid_file_rejected(api_client, isolated_storage):
    response = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("payload.exe", b"MZ-not-a-document", "application/x-msdownload")},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_empty_file_rejected(api_client, isolated_storage):
    response = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 422


def test_duplicate_content_returns_same_document(
    api_client, company_factory, isolated_storage
):
    company = company_factory("DUPCO")
    pdf_bytes = _minimal_pdf()

    first = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("a.pdf", pdf_bytes, "application/pdf")},
        data={"company_id": str(company.id)},
    )
    second = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("b.pdf", pdf_bytes, "application/pdf")},
        data={"company_id": str(company.id)},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
