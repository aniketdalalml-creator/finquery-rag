"""Standalone section-based chunking service.

Reads a document's stored `document_sections` rows, splits each section's
text into token-bounded chunks (with a small configurable overlap) and
writes `document_chunks` rows. Section rows and pages are never modified.

- Chunk size / overlap default to `config.CHUNK_SIZE` / `config.CHUNK_OVERLAP`
  (both in tokens, counted with `count_tokens`, tiktoken cl100k_base or a
  chars/4 fallback).
- Provenance: every chunk keeps its `section_id` plus the section's
  page span; `chunk_metadata` records the section title, type and parent path.
- `chunk_index` is renumbered globally per document in reading order
  (sections ordered by page_start, matching DocumentSectionRepository).
- Re-running with `replace=True` (default) deletes the document's previous
  chunks first so reruns never duplicate.
"""

from __future__ import annotations

import logging
import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import config
from app.core.errors import NotFoundError
from app.ingestion.chunking.chunker import count_tokens
from app.models.document import Document, DocumentChunk, DocumentSection

logger = logging.getLogger(__name__)

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


class DocumentChunkingService:
    """Split stored sections of a processed document into text chunks."""

    def __init__(
        self,
        session: Session,
        chunk_size: int | None = None,
        overlap_tokens: int | None = None,
    ) -> None:
        self.session = session
        self.chunk_size = (
            chunk_size if chunk_size is not None else config.CHUNK_SIZE
        )
        self.overlap_tokens = (
            overlap_tokens if overlap_tokens is not None else config.CHUNK_OVERLAP
        )
        if self.chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        if not 0 <= self.overlap_tokens < self.chunk_size:
            raise ValueError("overlap_tokens must satisfy 0 <= overlap < chunk_size")

    def run(
        self, document_id: int, replace: bool = True
    ) -> dict[str, int]:
        """Chunk every non-empty section of the document.

        Returns counts: sections seen, sections actually chunked, chunks written.
        """
        document = self.session.get(Document, document_id)
        if document is None:
            raise NotFoundError("Document", document_id)

        sections = (
            self.session.scalars(
                select(DocumentSection)
                .where(DocumentSection.document_id == document_id)
                .order_by(
                    DocumentSection.page_start.is_(None),
                    DocumentSection.page_start,
                    DocumentSection.id,
                )
            ).all()
        )

        if replace:
            # Flush the deletes before inserting so the unique
            # (document_id, chunk_index) constraint can never trip.
            self.session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            self.session.flush()

        chunks: list[DocumentChunk] = []
        chunked_sections = 0
        next_index = 0
        for section in sections:
            pieces = self._split_section_text(section.text or "")
            if not pieces:
                continue  # empty/whitespace-only sections produce no chunks
            chunked_sections += 1
            path = self._section_path(section)
            for piece in pieces:
                chunks.append(
                    DocumentChunk(
                        document_id=document_id,
                        section_id=section.id,
                        chunk_index=next_index,
                        chunk_type="text",
                        text=piece,
                        token_count=count_tokens(piece),
                        page_start=section.page_start,
                        page_end=section.page_end,
                        chunk_metadata={
                            "section_title": section.section_title,
                            "section_type": section.section_type,
                            "section_path": path,
                        },
                    )
                )
                next_index += 1

        self.session.add_all(chunks)
        self.session.flush()
        logger.info(
            "chunked document_id=%s sections=%d/%d chunks=%d size=%d overlap=%d",
            document_id,
            chunked_sections,
            len(sections),
            len(chunks),
            self.chunk_size,
            self.overlap_tokens,
        )
        return {
            "sections": len(sections),
            "sections_chunked": chunked_sections,
            "chunks": len(chunks),
        }

    # ── splitting ────────────────────────────────────────────────

    def _split_section_text(self, text: str) -> list[str]:
        if not text.strip():
            return []
        sentences: list[str] = []
        for paragraph in text.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            sentences.extend(
                s.strip() for s in _SENTENCE_BOUNDARY.split(paragraph) if s.strip()
            )
        return self._pack_sentences(sentences)

    def _pack_sentences(self, sentences: list[str]) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []
        current_tokens = 0

        def flush() -> None:
            nonlocal current, current_tokens
            if current:
                chunks.append(" ".join(current))
            current, current_tokens = [], 0

        for sentence in sentences:
            tokens = count_tokens(sentence)
            if tokens > self.chunk_size:
                flush()
                chunks.extend(self._hard_split(sentence))
                continue
            if current and current_tokens + tokens > self.chunk_size:
                # Capture the overlap tail BEFORE flushing clears `current`.
                tail, tail_tokens = [], 0
                for prev in reversed(current):
                    prev_tokens = count_tokens(prev)
                    if tail and tail_tokens + prev_tokens > self.overlap_tokens:
                        break
                    tail.insert(0, prev)
                    tail_tokens += prev_tokens
                    if tail_tokens >= self.overlap_tokens:
                        break
                flush()
                current, current_tokens = list(tail), tail_tokens
            current.append(sentence)
            current_tokens += tokens
        flush()
        return chunks

    def _hard_split(self, sentence: str) -> list[str]:
        """Word-window fallback for a single oversized sentence."""
        words = sentence.split()
        windows: list[str] = []
        current: list[str] = []
        current_tokens = 0
        for word in words:
            tokens = count_tokens(word + " ")
            if current and current_tokens + tokens > self.chunk_size:
                windows.append(" ".join(current))
                current, current_tokens = [], 0
            current.append(word)
            current_tokens += tokens
        if current:
            windows.append(" ".join(current))
        return windows

    # ── provenance helpers ───────────────────────────────────────

    @staticmethod
    def _section_path(section: DocumentSection) -> list[str]:
        titles = [section.section_title]
        parent = section.parent
        seen: set[int] = set()
        while parent is not None and parent.id not in seen:
            seen.add(parent.id)
            titles.append(parent.section_title)
            parent = parent.parent
        return list(reversed(titles))
