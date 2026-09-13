"""User ownership isolation for companies and documents."""

from __future__ import annotations


def _register_and_login(client, email: str, password: str = "StrongPassword123!"):
    assert client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    ).status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def test_users_cannot_see_each_others_companies(api_client):
    token_a = _register_and_login(api_client, "owner-a@example.com")
    api_client.headers["Authorization"] = f"Bearer {token_a}"
    created = api_client.post(
        "/api/v1/companies",
        json={"legal_name": "Alpha Holdings Inc", "ticker": "ALPH"},
    )
    assert created.status_code == 201, created.text
    company_id = created.json()["id"]

    token_b = _register_and_login(api_client, "owner-b@example.com")
    api_client.headers["Authorization"] = f"Bearer {token_b}"
    listing = api_client.get("/api/v1/companies")
    assert listing.status_code == 200
    assert listing.json()["items"] == []
    assert api_client.get(f"/api/v1/companies/{company_id}").status_code == 404

    api_client.headers["Authorization"] = f"Bearer {token_a}"
    listing_a = api_client.get("/api/v1/companies")
    assert listing_a.status_code == 200
    assert [c["id"] for c in listing_a.json()["items"]] == [company_id]


def test_users_cannot_see_each_others_documents(api_client):
    token_a = _register_and_login(api_client, "docs-a@example.com")
    api_client.headers["Authorization"] = f"Bearer {token_a}"
    company = api_client.post(
        "/api/v1/companies",
        json={"legal_name": "DocCo Inc", "ticker": "DOCA"},
    ).json()
    document = api_client.post(
        "/api/v1/documents",
        json={
            "company_id": company["id"],
            "document_type": "10-K",
            "title": "Private Filing",
        },
    )
    assert document.status_code == 201, document.text
    document_id = document.json()["id"]

    token_b = _register_and_login(api_client, "docs-b@example.com")
    api_client.headers["Authorization"] = f"Bearer {token_b}"
    assert api_client.get("/api/v1/documents").json() == []
    assert api_client.get(f"/api/v1/documents/{document_id}").status_code == 404

    api_client.headers["Authorization"] = f"Bearer {token_a}"
    listed = api_client.get("/api/v1/documents")
    assert [d["id"] for d in listed.json()] == [document_id]


def test_stats_are_scoped_to_current_user(api_client):
    token_a = _register_and_login(api_client, "stats-a@example.com")
    api_client.headers["Authorization"] = f"Bearer {token_a}"
    api_client.post(
        "/api/v1/companies",
        json={"legal_name": "Stats Co", "ticker": "STAA"},
    )
    token_b = _register_and_login(api_client, "stats-b@example.com")
    api_client.headers["Authorization"] = f"Bearer {token_b}"
    empty = api_client.get("/api/v1/stats/dashboard")
    assert empty.status_code == 200
    assert empty.json() == {
        "documents": 0,
        "companies": 0,
        "financial_metrics": 0,
    }
