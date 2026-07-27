"""Tests for api.main FastAPI endpoints using FastAPI's TestClient.

The pipeline is monkeypatched so no Groq or Jina API calls are made.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    # Build a fake pipeline that doesn't hit any external services.
    fake_pipeline = MagicMock()
    fake_pipeline.is_ready.return_value = True
    fake_pipeline.get_stats.return_value = {
        "total_documents": 12,
        "collection_name": "financial_docs",
        "embedding_model": "jina-embeddings-v2-base-en",
        "embedding_api": "Jina AI (cloud)",
        "vectorstore_path": "vectorstore/chroma_db",
    }
    fake_pipeline.ingest_documents.return_value = {
        "status": "success",
        "chunks_added": 12,
        "sources": ["apple_10k_summary.txt"],
        "message": "Documents ingested successfully",
    }
    fake_pipeline.query.return_value = {
        "question": "What was total revenue?",
        "answer": "Apple's total net sales were $394.3 billion in fiscal 2023.",
        "sources": [
            {
                "filename": "apple_10k_summary.txt",
                "relevance_score": 0.91,
                "snippet": "Total net sales $394.3 billion ...",
            }
        ],
        "context_chunks": 1,
        "model": "llama3-8b-8192",
    }
    fake_pipeline.reset.return_value = {
        "status": "cleared",
        "message": "Vectorstore cleared. Re-run ingest to use again.",
    }

    import api.main as api_main

    monkeypatch.setattr(api_main, "pipeline", fake_pipeline)
    return TestClient(api_main.app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["pipeline_ready"] is True
    assert body["total_chunks"] == 12


def test_ingest(client):
    r = client.post("/ingest", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["chunks_added"] == 12
    assert "apple_10k_summary.txt" in body["sources"]


def test_query(client):
    r = client.post("/query", json={"question": "What was total revenue?"})
    assert r.status_code == 200
    body = r.json()
    assert "394.3 billion" in body["answer"]
    assert body["sources"][0]["filename"] == "apple_10k_summary.txt"
    assert body["model"] == "llama3-8b-8192"


def test_query_validation_short_question(client):
    r = client.post("/query", json={"question": "hi"})
    assert r.status_code == 422

    r2 = client.post("/query", json={"question": "  hi  "})
    assert r2.status_code == 422


def test_reset(client):
    r = client.delete("/reset")
    assert r.status_code == 200
    assert r.json()["status"] == "cleared"


def test_documents(client):
    r = client.get("/documents")
    assert r.status_code == 200
    body = r.json()
    assert body["total_documents"] == 12
    assert body["embedding_api"] == "Jina AI (cloud)"
