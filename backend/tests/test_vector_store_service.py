"""Tests for the Qdrant vector store (client mocked — no backend needed)."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.vector_store_service import (
    QdrantVectorStore,
    VectorStore,
)


def make_chunk(chunk_id: int, document_id: int = 7, **overrides):
    defaults = dict(
        id=chunk_id,
        document_id=document_id,
        section_id=3,
        page_start=10,
        page_end=12,
        chunk_type="text",
        text=f"chunk {chunk_id} body",
        chunk_index=chunk_id,
        embedding_model="fake-model",
        embedding_vector=[0.1, 0.2, 0.3],
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_is_a_vector_store():
    assert isinstance(QdrantVectorStore(client=MagicMock()), VectorStore)


def test_ensure_collection_creates_when_missing():
    client = MagicMock()
    # get_collection raises → collection missing
    client.get_collection.side_effect = RuntimeError("missing")
    store = QdrantVectorStore(client=client)

    created = store.ensure_collection(vector_size=768)

    assert created is True
    args, kwargs = client.create_collection.call_args
    assert kwargs["vectors_config"].size == 768


def test_ensure_collection_skips_when_present():
    client = MagicMock()  # get_collection succeeds → exists
    store = QdrantVectorStore(client=client)

    assert store.ensure_collection() is False
    client.create_collection.assert_not_called()


def test_health_check_reflects_backend():
    healthy = QdrantVectorStore(client=MagicMock())
    assert healthy.health_check() is True

    broken_client = MagicMock()
    broken_client.get_collections.side_effect = RuntimeError("down")
    assert QdrantVectorStore(client=broken_client).health_check() is False


def test_upsert_stores_chunk_id_and_metadata():
    client = MagicMock()
    store = QdrantVectorStore(client=client)

    written = store.upsert_chunks([make_chunk(101), make_chunk(102)])

    assert written == 2
    points = client.upsert.call_args.kwargs["points"]
    assert [p.id for p in points] == [101, 102]
    payload = points[0].payload
    assert payload["document_id"] == 7
    assert payload["section_id"] == 3
    assert payload["page_start"] == 10
    assert payload["page_end"] == 12
    assert payload["chunk_type"] == "text"
    assert payload["text"] == "chunk 101 body"


def test_upsert_skips_unembedded_chunks():
    client = MagicMock()
    store = QdrantVectorStore(client=client)

    unembedded = make_chunk(103, embedding_vector=None)
    assert store.upsert_chunks([make_chunk(104), unembedded]) == 1
    points = client.upsert.call_args.kwargs["points"]
    assert [p.id for p in points] == [104]


def test_delete_document_targets_payload_filter():
    from qdrant_client import models as qm

    client = MagicMock()
    store = QdrantVectorStore(client=client)

    store.delete_document(document_id=42)

    kwargs = client.delete.call_args.kwargs
    selector = kwargs["points_selector"]
    condition = selector.filter.must[0]
    assert condition.key == "document_id"
    assert condition.match.value == 42


def test_missing_url_falls_back_to_local_mode():
    with patch("qdrant_client.QdrantClient") as client_cls:
        QdrantVectorStore(url="", local_path=r"C:\tmp\qdrant-test")
    _, kwargs = client_cls.call_args
    assert kwargs["path"] == r"C:\tmp\qdrant-test"
    assert "url" not in kwargs


def test_invalid_url_scheme_rejected():
    with pytest.raises(ValueError):
        QdrantVectorStore(url="ftp://not-a-qdrant-host")
