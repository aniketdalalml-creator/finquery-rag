"""Jina AI embedding client and ChromaDB persistence — API only, no local models."""

from __future__ import annotations

import logging
import os
from typing import Any, List

import requests
from langchain_core.documents import Document

from config.config import config

logger = logging.getLogger(__name__)


def _sanitize_metadata(meta: dict) -> dict:
    """Chroma metadata values must be str, int, float, or bool."""
    out: dict[str, Any] = {}
    for key, val in meta.items():
        if val is None:
            out[key] = ""
        elif isinstance(val, (str, int, float, bool)):
            out[key] = val
        else:
            out[key] = str(val)
    return out


class JinaEmbedder:
    """Calls Jina AI Embeddings API — no local model download."""

    def __init__(self) -> None:
        if not config.JINA_API_KEY:
            logger.warning("JINA_API_KEY not set. Embeddings will fail.")
        self.headers = {
            "Authorization": f"Bearer {config.JINA_API_KEY}",
            "Content-Type": "application/json",
        }
        logger.info("Jina embedder ready: model=%s", config.JINA_EMBEDDING_MODEL)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Call Jina AI API to get embeddings for a list of texts.

        Returns one vector per input string. Batches in groups of 100
        to stay within typical API limits.
        """
        all_embeddings: List[List[float]] = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            payload = {"model": config.JINA_EMBEDDING_MODEL, "input": batch}
            response = requests.post(
                config.JINA_API_URL,
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(embeddings)
            logger.info(
                "Embedded batch %s: %s texts", i // batch_size + 1, len(batch)
            )
        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        return self.embed_texts([query])[0]


class JinaEmbeddingFunction:
    """Jina API batch embedder used by ``VectorStoreManager`` (not registered with Chroma)."""

    def __init__(self) -> None:
        self.jina = JinaEmbedder()

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.jina.embed_texts(input)


class VectorStoreManager:
    """Manages ChromaDB vector store with Jina AI embeddings."""

    def __init__(self) -> None:
        import chromadb

        os.makedirs(config.VECTORSTORE_PATH, exist_ok=True)
        self.embedding_fn = JinaEmbeddingFunction()
        self.client = chromadb.PersistentClient(path=config.VECTORSTORE_PATH)
        self.collection = None
        logger.info("VectorStoreManager initialized with Jina AI embeddings")

    def _get_or_create_collection(self):
        """
        Get or create the Chroma collection.

        Embeddings are supplied explicitly on upsert/query (Jina API), so no
        ``embedding_function`` is attached to the collection — avoids Chroma 1.x
        schema/``name`` issues with custom embedding classes.
        """
        if self.collection is not None:
            return self.collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:
            if "name" not in str(exc).lower():
                raise
            logger.warning(
                "Recreating collection (legacy embedding config): %s", exc
            )
            try:
                self.client.delete_collection(config.COLLECTION_NAME)
            except Exception:
                pass
            self.collection = self.client.create_collection(
                name=config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self.collection

    def add_documents(self, chunks: List[Document]) -> int:
        """Embed chunks via Jina API and store in ChromaDB."""
        collection = self._get_or_create_collection()
        texts = [c.page_content for c in chunks]
        metadatas = [_sanitize_metadata(c.metadata) for c in chunks]
        ids = [f"chunk_{hash(t) % 100000000}" for t in texts]

        logger.info("Embedding %s chunks via Jina AI API...", len(texts))
        embeddings = self.embedding_fn(input=texts)

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Stored %s chunks in ChromaDB", len(chunks))
        return len(chunks)

    def query(self, query_text: str, n_results: int | None = None) -> dict:
        """Embed query via Jina API and search ChromaDB."""
        k = n_results or config.TOP_K
        collection = self._get_or_create_collection()
        query_embedding = self.embedding_fn.jina.embed_query(query_text)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        return results

    def vectorstore_exists(self) -> bool:
        """Return True if the collection exists and contains at least one row."""
        try:
            col = self.client.get_collection(config.COLLECTION_NAME)
            return col.count() > 0
        except Exception:
            return False

    def delete_collection(self) -> None:
        """Delete the backing collection and reset the cached handle."""
        try:
            self.client.delete_collection(config.COLLECTION_NAME)
            self.collection = None
            logger.info("Collection deleted")
        except Exception as e:
            logger.warning("Delete error: %s", e)

    def get_collection_stats(self) -> dict:
        """Return human-readable stats for the active collection."""
        try:
            col = self._get_or_create_collection()
            count = col.count()
        except Exception:
            count = 0
        return {
            "total_documents": count,
            "collection_name": config.COLLECTION_NAME,
            "embedding_model": config.JINA_EMBEDDING_MODEL,
            "embedding_api": "Jina AI (cloud)",
            "vectorstore_path": config.VECTORSTORE_PATH,
        }
