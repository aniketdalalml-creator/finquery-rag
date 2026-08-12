"""Tests for src.chunker.DocumentChunker."""
from app.rag.chunker import DocumentChunker


def test_chunker_splits_documents(sample_documents):
    chunker = DocumentChunker()
    chunks = chunker.chunk_documents(sample_documents)
    assert len(chunks) >= len(sample_documents)
    for chunk in chunks:
        assert "chunk_index" in chunk.metadata
        assert "chunk_size" in chunk.metadata
        assert chunk.metadata["chunk_size"] == len(chunk.page_content)


def test_chunk_text_returns_documents(sample_text):
    chunker = DocumentChunker()
    chunks = chunker.chunk_text(sample_text, metadata={"source": "inline"})
    assert len(chunks) >= 1
    assert chunks[0].metadata["source"] == "inline"


def test_chunk_stats(sample_documents):
    chunker = DocumentChunker()
    chunks = chunker.chunk_documents(sample_documents)
    stats = chunker.get_chunk_stats(chunks)
    assert stats["total_chunks"] == len(chunks)
    assert stats["min_size"] <= stats["avg_size"] <= stats["max_size"]
    assert stats["total_chars"] > 0
