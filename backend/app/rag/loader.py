"""Load financial PDF and text files into LangChain Documents."""

from __future__ import annotations

import logging
import os
from typing import List

from langchain_core.documents import Document

from app.core.config import config

logger = logging.getLogger(__name__)


class FinancialDocumentLoader:
    """Loads PDF and TXT files from disk into LangChain `Document` objects."""

    def load_pdf(self, file_path: str) -> List[Document]:
        """Load a PDF; metadata includes basename and file_type pdf."""
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(file_path)
        documents = loader.load()
        basename = os.path.basename(file_path)
        for doc in documents:
            doc.metadata["source"] = basename
            doc.metadata["file_type"] = "pdf"
        logger.info("Loaded %s pages from %s", len(documents), basename)
        return documents

    def load_text(self, file_path: str) -> List[Document]:
        """Load a UTF-8 text file as a single Document."""
        basename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info("Loaded text: %s (%s chars)", basename, len(content))
        return [
            Document(
                page_content=content,
                metadata={"source": basename, "file_type": "text"},
            )
        ]

    def load_directory(self, dir_path: str) -> List[Document]:
        """Load all `.pdf` and `.txt` files under ``dir_path`` (non-recursive)."""
        if not os.path.isdir(dir_path):
            logger.warning("Directory does not exist: %s", dir_path)
            return []

        combined: List[Document] = []
        for name in sorted(os.listdir(dir_path)):
            fp = os.path.join(dir_path, name)
            if not os.path.isfile(fp):
                continue
            lower = name.lower()
            if lower.endswith(".pdf"):
                combined.extend(self.load_pdf(fp))
            elif lower.endswith(".txt"):
                combined.extend(self.load_text(fp))

        logger.info("Loaded %s documents from %s", len(combined), dir_path)
        return combined

    def load_sample_docs(self) -> List[Document]:
        """Load documents from ``config.SAMPLE_DOCS_PATH``."""
        return self.load_directory(config.SAMPLE_DOCS_PATH)

    def get_document_metadata(self, documents: List[Document]) -> dict:
        """Summarize loaded documents: counts, total characters, unique sources."""
        sources = []
        seen = set()
        total_chars = 0
        for doc in documents:
            total_chars += len(doc.page_content)
            src = doc.metadata.get("source", "")
            if src and src not in seen:
                seen.add(src)
                sources.append(src)
        return {
            "total_docs": len(documents),
            "total_chars": total_chars,
            "sources": sources,
        }

    def load_for_ingest(self, file_paths: list[str] | None) -> List[Document]:
        """
        Resolve documents for RAG ingest: explicit ``file_paths``, else any files
        under ``config.RAW_DOCS_PATH``, else bundled sample docs.
        """
        if file_paths:
            docs: List[Document] = []
            for fp in file_paths:
                if fp.lower().endswith(".pdf"):
                    docs.extend(self.load_pdf(fp))
                else:
                    docs.extend(self.load_text(fp))
            return docs

        raw_docs = self.load_directory(config.RAW_DOCS_PATH)
        if raw_docs:
            logger.info(
                "Ingesting %s document(s) from %s",
                len(raw_docs),
                config.RAW_DOCS_PATH,
            )
            return raw_docs

        logger.info("No files in %s; using sample_docs", config.RAW_DOCS_PATH)
        return self.load_sample_docs()
