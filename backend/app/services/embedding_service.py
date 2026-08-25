"""Chunk embedding service.

Generates embeddings for `document_chunks` rows that don't have one yet
and stores the vector, a stable vector identifier and the model name on
the chunk row itself.

- The provider is behind `EmbeddingProvider` (generate / generate_batch),
  so swapping Jina for another model/provider is a config change.
- Chunks are processed in configurable batches; every successful batch is
  committed immediately so progress survives later failures.
- Provider failures never delete or corrupt chunks: failed batches roll
  back and stay pending (embeddable by a later run).
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import config
from app.models.document import DocumentChunk

logger = logging.getLogger(__name__)

# Stable namespace so embedding ids are reproducible across runs.
_EMBEDDING_NS = uuid.UUID("6f1d2c34-7a8e-4b5f-9c0d-1e2f3a4b5c6d")


def vector_identifier(model: str, chunk_id: int) -> str:
    """Deterministic identifier for one (model, chunk) pair."""
    return str(uuid.uuid5(_EMBEDDING_NS, f"{model}:{chunk_id}"))


class EmbeddingProvider(ABC):
    """Minimal contract for an embedding backend."""

    model_name: str

    @abstractmethod
    def generate(self, text: str) -> list[float]:
        """Embed a single text."""

    @abstractmethod
    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in order; returns one vector per input."""


class JinaEmbeddingProvider(EmbeddingProvider):
    """Jina AI embeddings API (same endpoint as the legacy RAG path)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        api_url: str | None = None,
        timeout_s: int = 30,
    ) -> None:
        self.api_key = api_key or config.EMBEDDING_API_KEY
        self.model_name = model or config.EMBEDDING_MODEL
        self.api_url = api_url or config.EMBEDDING_API_URL
        self.timeout_s = timeout_s
        if not self.api_key:
            raise RuntimeError(
                "No embedding API key configured — set EMBEDDING_API_KEY "
                "(or JINA_API_KEY) in the environment."
            )

    def generate(self, text: str) -> list[float]:
        return self.generate_batch([text])[0]

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = {"model": self.model_name, "input": list(texts)}
        response = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        data = response.json()["data"]
        # API returns items sorted by input index.
        return [item["embedding"] for item in data]


class NullEmbeddingProvider(EmbeddingProvider):
    """Deterministic offline provider (dev/tests without network)."""

    def __init__(self, dimensions: int = 8) -> None:
        self.dimensions = dimensions
        self.model_name = f"null-embed-{dimensions}"

    def generate(self, text: str) -> list[float]:
        return self.generate_batch([text])[0]

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            seed = sum(ord(ch) for ch in text) % 251
            vectors.append([((seed + i) % 97) / 97 for i in range(self.dimensions)])
        return vectors


def get_embedding_provider() -> EmbeddingProvider:
    """Build the configured provider (env: EMBEDDING_PROVIDER)."""
    provider = config.EMBEDDING_PROVIDER
    if provider == "jina":
        return JinaEmbeddingProvider()
    if provider == "null":
        return NullEmbeddingProvider()
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider!r}")


class ChunkEmbeddingService:
    """Embed pending document_chunks in batches, storing results inline."""

    def __init__(
        self,
        session: Session,
        provider: EmbeddingProvider | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.session = session
        self.provider = provider or get_embedding_provider()
        self.batch_size = batch_size or config.EMBEDDING_BATCH_SIZE
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")

    def run(self, document_id: int | None = None) -> dict[str, int]:
        """Embed all pending chunks (optionally scoped to one document).

        Returns counts: embedded / failed / skipped_empty / pending.
        """
        pending = self._pending_chunks(document_id)
        embeddable = [c for c in pending if (c.text or "").strip()]
        skipped_empty = len(pending) - len(embeddable)

        embedded = 0
        failed = 0
        for start in range(0, len(embeddable), self.batch_size):
            batch = embeddable[start : start + self.batch_size]
            try:
                vectors = self.provider.generate_batch([c.text for c in batch])
                if len(vectors) != len(batch):
                    raise RuntimeError(
                        f"provider returned {len(vectors)} vectors "
                        f"for {len(batch)} inputs"
                    )
            except Exception as exc:  # noqa: BLE001 — any failure keeps chunks intact
                # Vectors are fetched before any write, so a failed batch has
                # no pending changes; only roll back if that ever changes.
                if self.session.new or self.session.dirty:
                    self.session.rollback()
                failed += len(batch)
                logger.warning(
                    "embedding batch failed (%d chunks): %s", len(batch), exc
                )
                continue
            for chunk, vector in zip(batch, vectors):
                self._apply(chunk, vector)
                embedded += 1
            # Commit per batch: progress persists even if a later batch fails.
            self.session.commit()

        logger.info(
            "embedding run done model=%s embedded=%d failed=%d skipped_empty=%d",
            self.provider.model_name,
            embedded,
            failed,
            skipped_empty,
        )
        return {
            "embedded": embedded,
            "failed": failed,
            "skipped_empty": skipped_empty,
            "pending": len(pending),
        }

    # ── internals ────────────────────────────────────────────────

    def _pending_chunks(
        self, document_id: int | None
    ) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.embedding_model.is_(None))
            .order_by(DocumentChunk.id)
        )
        if document_id is not None:
            stmt = stmt.where(DocumentChunk.document_id == document_id)
        return list(self.session.scalars(stmt).all())

    def _apply(self, chunk: DocumentChunk, vector: list[float]) -> None:
        chunk.embedding_vector = vector
        chunk.embedding_model = self.provider.model_name
        chunk.embedding_id = vector_identifier(self.provider.model_name, chunk.id)
        chunk.embedded_at = datetime.now(timezone.utc)
