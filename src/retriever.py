"""Retrieve relevant chunks from Chroma using Jina query embeddings."""

from __future__ import annotations

import logging
from typing import List, Tuple

from langchain_core.documents import Document

from src.embedder import VectorStoreManager

logger = logging.getLogger(__name__)

# Map common analyst questions to 10-K wording (e.g. "revenue" → "net sales").
_QUERY_EXPANSIONS: dict[str, str] = {
    "revenue": "total net sales net sales",
    "sales": "net sales total net sales",
    "income": "net sales revenue earnings",
    "cash": "cash equivalents marketable securities liquidity",
    "debt": "long-term debt borrowings",
    "r&d": "research and development expense",
    "rd": "research and development expense",
    "risk": "risk factors ITEM 1A",
    "margin": "gross margin profitability",
}


class FinancialRetriever:
    """Retrieves relevant document chunks using Jina embeddings + ChromaDB."""

    def __init__(self, vsm: VectorStoreManager):
        self.vsm = vsm
        logger.info("Retriever initialized")

    @staticmethod
    def _expand_query(query: str) -> str:
        """Add SEC-style terms so embedding search matches 10-K language."""
        q_lower = query.lower()
        hints: list[str] = []
        for keyword, expansion in _QUERY_EXPANSIONS.items():
            if keyword in q_lower:
                hints.append(expansion)
        if not hints:
            return query
        return f"{query} {' '.join(hints)}"

    @staticmethod
    def _dedupe_docs(
        docs_with_scores: List[Tuple[Document, float]],
    ) -> List[Tuple[Document, float]]:
        seen: set[str] = set()
        unique: List[Tuple[Document, float]] = []
        for doc, score in docs_with_scores:
            key = doc.page_content.strip()
            if key in seen:
                continue
            seen.add(key)
            unique.append((doc, score))
        return unique

    def retrieve(self, query: str) -> List[Document]:
        """Retrieve top-K chunks for a query."""
        search_q = self._expand_query(query)
        results = self.vsm.query(search_q)
        docs: List[Document] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        for text, meta in zip(documents, metadatas):
            docs.append(Document(page_content=text, metadata=meta or {}))
        logger.info(
            "Query: '%s' → %s chunks retrieved", query[:50], len(docs)
        )
        return docs

    def retrieve_with_scores(self, query: str) -> List[Tuple[Document, float]]:
        """Retrieve chunks with their similarity distances."""
        search_q = self._expand_query(query)
        if search_q != query:
            logger.info("Search query expanded: %s", search_q[:100])
        results = self.vsm.query(search_q)
        docs_with_scores: List[Tuple[Document, float]] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for text, meta, dist in zip(documents, metadatas, distances):
            doc = Document(page_content=text, metadata=meta or {})
            docs_with_scores.append((doc, float(dist)))
        return self._dedupe_docs(docs_with_scores)

    def format_context(self, documents: List[Document]) -> str:
        """Format retrieved docs into a single context string."""
        parts = []
        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            parts.append(f"📄 Source: {source}\n{doc.page_content}\n---")
        return "\n".join(parts)
