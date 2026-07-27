"""Tests for src.embedder — uses monkeypatched Jina API so no network calls happen."""
from unittest.mock import patch, MagicMock

import pytest


def _fake_jina_response(batch_size: int, dim: int = 768):
    """Build a fake requests.Response-like object for Jina embeddings."""
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "data": [{"embedding": [0.01] * dim} for _ in range(batch_size)]
    }
    return response


def test_jina_embedder_batches_and_returns_vectors():
    from src.embedder import JinaEmbedder

    with patch("src.embedder.requests.post") as mock_post:
        mock_post.side_effect = lambda *a, **kw: _fake_jina_response(
            batch_size=len(kw["json"]["input"])
        )
        embedder = JinaEmbedder()
        vectors = embedder.embed_texts(["hello", "world", "finquery"])
        assert len(vectors) == 3
        assert all(len(v) == 768 for v in vectors)


def test_jina_embedder_embed_query():
    from src.embedder import JinaEmbedder

    with patch("src.embedder.requests.post") as mock_post:
        mock_post.return_value = _fake_jina_response(batch_size=1)
        embedder = JinaEmbedder()
        vector = embedder.embed_query("what was total revenue?")
        assert isinstance(vector, list)
        assert len(vector) == 768


def test_vectorstore_add_without_chroma_embedding_function(sample_documents):
    """Collection is created without embedding_function; vectors passed on upsert."""
    from unittest.mock import MagicMock, patch

    from src.embedder import VectorStoreManager

    mock_collection = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    with patch("chromadb.PersistentClient", return_value=mock_client):
        with patch("src.embedder.JinaEmbeddingFunction") as mock_ef_cls:
            mock_ef = MagicMock()
            mock_ef.return_value = [[0.1] * 768]
            mock_ef_cls.return_value = mock_ef
            vsm = VectorStoreManager()
            from src.chunker import DocumentChunker

            chunks = DocumentChunker().chunk_documents(sample_documents[:1])
            n = vsm.add_documents(chunks)
            assert n == 1
            mock_client.get_or_create_collection.assert_called_once()
            call_kw = mock_client.get_or_create_collection.call_args.kwargs
            assert "embedding_function" not in call_kw
            mock_collection.upsert.assert_called_once()
