"""Tests for VectorRetriever (Qdrant client mocked)."""

from types import SimpleNamespace

import pytest

from app.services.retrieval_service import RetrievedChunk, VectorRetriever


def make_store(hit_points):
    """A fake VectorStore exposing a mocked qdrant client."""
    client = MagicMock = None  # placeholder to keep flake tools quiet
    del client

    def query_points(**kwargs):
        return SimpleNamespace(points=hit_points)

    return SimpleNamespace(
        collection="document_chunks",
        client=SimpleNamespace(query_points=query_points),
    )


def hit(point_id, score, document_id=1, text="revenue text"):
    return SimpleNamespace(
        id=point_id,
        score=score,
        payload={
            "document_id": document_id,
            "section_id": 5,
            "page_start": 10,
            "page_end": 11,
            "chunk_type": "text",
            "text": text,
        },
    )


def test_search_returns_relevant_chunks_with_metadata():
    store = make_store([hit(11, 0.93), hit(12, 0.81)])
    retriever = VectorRetriever(store=store)

    results = retriever.search([0.1, 0.2], top_k=2)

    assert results == [
        RetrievedChunk(
            chunk_id=11,
            score=0.93,
            text="revenue text",
            document_id=1,
            section_id=5,
            page_start=10,
            page_end=11,
        ),
        RetrievedChunk(
            chunk_id=12,
            score=0.81,
            text="revenue text",
            document_id=1,
            section_id=5,
            page_start=10,
            page_end=11,
        ),
    ]


def test_top_k_limits_results():
    captured = {}

    def query_points(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(points=[hit(1, 0.9)])

    store = SimpleNamespace(
        collection="document_chunks",
        client=SimpleNamespace(query_points=query_points),
    )
    retriever = VectorRetriever(store=store)

    results = retriever.search([0.1], top_k=1)

    assert len(results) == 1
    assert captured["limit"] == 1


def test_document_filter_builds_payload_condition():
    from qdrant_client import models as qm

    captured = {}

    def query_points(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(points=[])

    store = SimpleNamespace(
        collection="document_chunks",
        client=SimpleNamespace(query_points=query_points),
    )

    VectorRetriever(store=store).search([0.1], top_k=3, document_id=9)

    condition = captured["query_filter"].must[0]
    assert isinstance(condition, qm.FieldCondition)
    assert condition.key == "document_id"
    assert condition.match.value == 9


def test_empty_index_returns_nothing():
    store = make_store([])
    results = VectorRetriever(store=store).search([0.1])
    assert results == []


def test_qdrant_failure_degrades_to_empty():
    def boom(**kwargs):
        raise RuntimeError("qdrant down")

    store = SimpleNamespace(
        collection="document_chunks",
        client=SimpleNamespace(query_points=boom),
    )
    results = VectorRetriever(store=store).search([0.1], top_k=4)
    assert results == []


def test_invalid_top_k_rejected():
    store = make_store([])
    with pytest.raises(ValueError):
        VectorRetriever(store=store).search([0.1], top_k=0)
