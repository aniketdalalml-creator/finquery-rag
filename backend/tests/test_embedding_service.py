"""Tests for the chunk embedding service (fake provider, no network)."""

import pytest

from app.models.document import Document, DocumentChunk
from app.services.embedding_service import (
    ChunkEmbeddingService,
    EmbeddingProvider,
    vector_identifier,
)


class FakeProvider(EmbeddingProvider):
    """Records calls; can be told to fail on specific texts."""

    model_name = "fake-model"

    def __init__(self, dimensions: int = 4, fail_on: set[str] | None = None) -> None:
        self.dimensions = dimensions
        self.fail_on = fail_on or set()
        self.calls: list[list[str]] = []

    def generate(self, text: str) -> list[float]:
        return self.generate_batch([text])[0]

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        for text in texts:
            if text in self.fail_on:
                raise RuntimeError(f"provider boom: {text!r}")
        return [[0.5] * self.dimensions for _ in texts]


@pytest.fixture
def make_chunks(db_session, company_factory, document_factory):
    def _make(texts: list[str]) -> Document:
        company = company_factory(f"EM{abs(hash(tuple(texts))) % 100000:05d}")
        document = document_factory(company=company, title="Embedding Target")
        for index, text in enumerate(texts):
            db_session.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    chunk_type="text",
                    text=text,
                )
            )
        db_session.flush()
        return document

    return _make


def chunks_of(db_session, document_id: int) -> list[DocumentChunk]:
    return (
        db_session.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )


def test_single_embedding_stored(db_session, make_chunks):
    document = make_chunks(["One chunk only."])
    provider = FakeProvider(dimensions=4)

    result = ChunkEmbeddingService(db_session, provider=provider).run(document.id)

    assert result["embedded"] == 1
    (chunk,) = chunks_of(db_session, document.id)
    assert chunk.embedding_vector == [0.5, 0.5, 0.5, 0.5]
    assert len(chunk.embedding_vector) == provider.dimensions
    assert chunk.embedding_model == "fake-model"
    assert chunk.embedding_id == vector_identifier("fake-model", chunk.id)
    assert chunk.embedded_at is not None
    # The abstraction's single-text path works too.
    assert provider.generate(chunk.text) == [0.5] * 4


def test_batch_embedding_groups_calls(db_session, make_chunks):
    document = make_chunks(["alpha body", "beta body", "gamma body"])
    provider = FakeProvider()

    result = ChunkEmbeddingService(db_session, provider=provider, batch_size=2).run(
        document.id
    )

    assert result["embedded"] == 3
    assert provider.calls == [["alpha body", "beta body"], ["gamma body"]]
    assert all(c.embedding_model == "fake-model" for c in chunks_of(db_session, document.id))


def test_empty_text_skipped_without_provider_call(db_session, make_chunks):
    document = make_chunks(["real content", "", "   "])
    provider = FakeProvider()

    result = ChunkEmbeddingService(db_session, provider=provider).run(document.id)

    assert result["embedded"] == 1
    assert result["skipped_empty"] == 2
    assert provider.calls == [["real content"]]
    rows = chunks_of(db_session, document.id)
    assert rows[0].embedding_model == "fake-model"
    assert rows[1].embedding_model is None and rows[1].embedding_vector is None
    assert rows[2].embedding_model is None and rows[2].embedding_vector is None


def test_provider_failure_keeps_chunks_and_recovers(db_session, make_chunks):
    document = make_chunks(["good one", "bad one", "good two"])
    failing = FakeProvider(fail_on={"bad one"})

    first = ChunkEmbeddingService(db_session, provider=failing, batch_size=1).run(
        document.id
    )

    assert first["embedded"] == 2
    assert first["failed"] == 1
    rows = {c.text: c for c in chunks_of(db_session, document.id)}
    assert rows["bad one"].embedding_vector is None  # still pending, not lost
    assert rows["good one"].embedding_model == "fake-model"

    # A later healthy run embeds the previously failed chunk.
    healthy = FakeProvider()
    second = ChunkEmbeddingService(db_session, provider=healthy).run(document.id)
    assert second["embedded"] == 1
    assert chunks_of(db_session, document.id)[1].embedding_vector == [0.5] * 4


def test_already_embedded_chunks_are_untouched(db_session, make_chunks):
    document = make_chunks(["only once"])
    provider = FakeProvider()
    service = ChunkEmbeddingService(db_session, provider=provider)

    service.run(document.id)
    before = chunks_of(db_session, document.id)[0]
    embedding_id = before.embedding_id
    calls_after_first = len(provider.calls)

    second = service.run(document.id)

    assert second["embedded"] == 0
    assert second["pending"] == 0
    after = chunks_of(db_session, document.id)[0]
    assert after.embedding_id == embedding_id
    assert len(provider.calls) == calls_after_first


def test_unknown_provider_rejected():
    from app.core import config as cfg

    original = cfg.config.EMBEDDING_PROVIDER
    cfg.config.EMBEDDING_PROVIDER = "does-not-exist"
    try:
        with pytest.raises(ValueError):
            from app.services.embedding_service import get_embedding_provider

            get_embedding_provider()
    finally:
        cfg.config.EMBEDDING_PROVIDER = original
