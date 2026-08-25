"""Vector store abstraction with a Qdrant implementation.

Qdrant is a disposable vector index over `document_chunks`; the relational
database (MySQL llm_db in this project) stays the source of truth. Points
use the chunk's primary key as ID, so re-upserting is idempotent.

Configuration (environment):
- QDRANT_URL        e.g. http://localhost:6333 — empty or "local" selects
                    embedded local mode persisting under QDRANT_LOCAL_PATH
- QDRANT_API_KEY    optional bearer key for Qdrant Cloud / secured servers
- QDRANT_COLLECTION collection name (default "document_chunks")
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from app.core.config import config
from app.models.document import DocumentChunk

logger = logging.getLogger(__name__)


class VectorStoreError(RuntimeError):
    """Raised when the vector store cannot be reached or configured."""


class VectorStore(ABC):
    """Minimal vector-index contract used by the retrieval service."""

    @abstractmethod
    def ensure_collection(self, vector_size: int | None = None) -> bool:
        """Create the collection if missing; True when it was created."""

    @abstractmethod
    def collection_exists(self) -> bool:
        """Whether the configured collection exists."""

    @abstractmethod
    def health_check(self) -> bool:
        """Whether the backend answers at all."""

    @abstractmethod
    def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Index embedded chunks; returns how many points were written."""

    @abstractmethod
    def delete_document(self, document_id: int) -> None:
        """Remove every vector belonging to one document."""


class QdrantVectorStore(VectorStore):
    """Qdrant-backed VectorStore (server or embedded local mode)."""

    def __init__(
        self,
        client=None,
        url: str | None = None,
        api_key: str | None = None,
        collection: str | None = None,
        local_path: str | None = None,
    ) -> None:
        from qdrant_client import QdrantClient

        self.collection = collection or config.QDRANT_COLLECTION
        if client is not None:
            self.client = client
            return

        url = url if url is not None else config.QDRANT_URL
        api_key = api_key if api_key is not None else config.QDRANT_API_KEY
        if url and url.strip().lower() != "local":
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(
                    f"Invalid QDRANT_URL {url!r}: expected http(s)://host[:port]"
                )
            self.client = QdrantClient(url=url, api_key=api_key or None)
        else:
            path = local_path or config.QDRANT_LOCAL_PATH
            logger.info("Qdrant local mode at %s", path)
            self.client = QdrantClient(path=path)

    # ── collection lifecycle ─────────────────────────────────────

    def collection_exists(self) -> bool:
        try:
            self.client.get_collection(self.collection)
            return True
        except Exception:  # noqa: BLE001 — any miss means "not there"
            return False

    def health_check(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Qdrant health check failed: %s", exc)
            return False

    def ensure_collection(self, vector_size: int | None = None) -> bool:
        from qdrant_client import models as qm

        size = vector_size or config.EMBEDDING_DIMENSION
        if self.collection_exists():
            return False
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qm.VectorParams(
                size=size, distance=qm.Distance.COSINE
            ),
        )
        logger.info("Created Qdrant collection %s (size=%d)", self.collection, size)
        return True

    # ── indexing ─────────────────────────────────────────────────

    def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:
        from qdrant_client import models as qm

        points = []
        for chunk in chunks:
            if not chunk.embedding_vector:
                continue  # never index an un-embedded chunk
            points.append(
                qm.PointStruct(
                    id=chunk.id,
                    vector=list(chunk.embedding_vector),
                    payload={
                        "document_id": chunk.document_id,
                        "section_id": chunk.section_id,
                        "page_start": chunk.page_start,
                        "page_end": chunk.page_end,
                        "chunk_type": chunk.chunk_type,
                        "text": chunk.text,
                        "chunk_index": chunk.chunk_index,
                        "embedding_model": chunk.embedding_model,
                    },
                )
            )
        if not points:
            return 0
        self.client.upsert(collection_name=self.collection, points=points)
        return len(points)

    def delete_document(self, document_id: int) -> None:
        from qdrant_client import models as qm

        self.client.delete(
            collection_name=self.collection,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="document_id",
                            match=qm.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )


def get_vector_store() -> VectorStore:
    return QdrantVectorStore()
