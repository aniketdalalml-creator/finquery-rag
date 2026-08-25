"""Vector similarity retrieval over the Qdrant index.

Pure nearest-neighbour search over chunk embeddings — no BM25, no hybrid
scoring, no reranking. Returns payload metadata alongside each hit so the
caller can cite provenance.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import config
from app.services.vector_store_service import VectorStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: int
    score: float
    text: str
    document_id: int | None
    section_id: int | None
    page_start: int | None
    page_end: int | None


class VectorRetriever:
    """Top-k similarity search against the configured vector store."""

    def __init__(self, store: VectorStore | None = None) -> None:
        self.store = store or self._default_store()

    @staticmethod
    def _default_store() -> VectorStore:
        # Imported lazily so tests can inject fakes without Qdrant installed.
        from app.services.vector_store_service import get_vector_store

        return get_vector_store()

    def search(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
        document_id: int | None = None,
    ) -> list[RetrievedChunk]:
        """Return the top_k most similar chunks, optionally scoped to a doc.

        Retrieval failures degrade to an empty result set instead of
        raising — callers answer "not enough information" rather than 500.
        """
        limit = config.TOP_K if top_k is None else top_k
        if limit < 1:
            raise ValueError("top_k must be >= 1")
        if not query_embedding:
            return []
        try:
            from qdrant_client import models as qm

            query_filter = None
            if document_id is not None:
                query_filter = qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="document_id",
                            match=qm.MatchValue(value=document_id),
                        )
                    ]
                )
            response = self.store.client.query_points(
                collection_name=self.store.collection,
                query=list(query_embedding),
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
            )
            return [
                RetrievedChunk(
                    chunk_id=int(point.id),
                    score=float(point.score),
                    text=str(point.payload.get("text", "")),
                    document_id=point.payload.get("document_id"),
                    section_id=point.payload.get("section_id"),
                    page_start=point.payload.get("page_start"),
                    page_end=point.payload.get("page_end"),
                )
                for point in response.points
            ]
        except Exception as exc:  # noqa: BLE001 — retrieval must not 500
            logger.warning("vector search failed: %s", exc)
            return []
