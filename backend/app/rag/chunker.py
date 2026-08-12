"""Split financial documents into overlapping chunks for embedding."""

from __future__ import annotations

import logging
from typing import List

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.core.config import config

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Splits documents into overlapping chunks for embedding."""

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        logger.info(
            "Chunker ready: size=%s, overlap=%s",
            config.CHUNK_SIZE,
            config.CHUNK_OVERLAP,
        )

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks and add chunk metadata."""
        chunks = self.splitter.split_documents(documents)
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_size"] = len(chunk.page_content)
        logger.info(
            "Created %s chunks from %s documents", len(chunks), len(documents)
        )
        return chunks

    def chunk_text(self, text: str, metadata: dict | None = None) -> List[Document]:
        """Chunk raw text directly."""
        meta = dict(metadata) if metadata else {}
        doc = Document(page_content=text, metadata=meta)
        return self.chunk_documents([doc])

    def get_chunk_stats(self, chunks: List[Document]) -> dict:
        """Return aggregate statistics for a list of chunks."""
        sizes = [len(c.page_content) for c in chunks]
        return {
            "total_chunks": len(chunks),
            "avg_size": int(sum(sizes) / len(sizes)) if sizes else 0,
            "min_size": min(sizes) if sizes else 0,
            "max_size": max(sizes) if sizes else 0,
            "total_chars": sum(sizes),
        }
