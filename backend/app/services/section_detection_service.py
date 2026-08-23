"""SectionDetectionService — reusable section detection over cleaned pages.

Reads ``document_pages.cleaned_text`` for a document, detects major
headings with :class:`~app.ingestion.sectioning.detector.SectionDetector`
(no LLM, no tables, no metrics, no chunks), and persists the hierarchy
into the existing ``document_sections`` table with parent links, page
ranges and verbatim body text.

Standalone on purpose: any caller (API route, pipeline stage, script)
can run it for one document without touching the rest of ingestion.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.ingestion.sectioning.detector import (
    DetectedSection,
    SectionDetector,
    _looks_like_generic_heading,
    _match_known,
)
from app.models.document import Document, DocumentPage, DocumentSection

logger = logging.getLogger(__name__)


@dataclass
class SectionDetectionSummary:
    """Outcome of one detection run for a document."""

    document_id: int
    sections_stored: int
    roots: int
    unknown_headings: int
    sections: list[DocumentSection]


@dataclass
class _HeadingHit:
    """A heading line located in the page stream."""

    page_number: int
    line_index: int
    depth: int  # 0 = root; grows for chained nested headings
    detected: DetectedSection | None = None


def _cleaned_pages(session: Session, document_id: int) -> dict[int, str]:
    """Page number → non-empty cleaned text (original text, untouched)."""
    rows = (
        session.query(DocumentPage)
        .filter(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
        .all()
    )
    return {
        row.page_number: row.cleaned_text
        for row in rows
        if row.cleaned_text and row.cleaned_text.strip()
    }


def _scan_heading_hits(
    cleaned_pages: dict[int, str], detect_generic: bool
) -> list[_HeadingHit]:
    """Replay the detector's per-line decisions to locate heading lines.

    Iterates pages/lines exactly like ``SectionDetector.detect`` so hit
    order aligns 1:1 with the detector's flat output.
    """
    hits: list[_HeadingHit] = []
    last_depth: int | None = None  # depth of most recent heading
    for page_number in sorted(cleaned_pages):
        lines = cleaned_pages[page_number].splitlines()
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            prev_blank = index == 0 or not lines[index - 1].strip()
            next_blank = index == len(lines) - 1 or not lines[index + 1].strip()

            match = _match_known(line)
            is_generic = (
                match is None
                and detect_generic
                and _looks_like_generic_heading(prev_blank, line, next_blank)
            )
            if match is None and not is_generic:
                continue

            top_level = bool(match[2]) if match else False
            if top_level or last_depth is None:
                # Top-level pattern, or no root yet: this starts a root.
                depth = 0
            else:
                # Mirror SectionDetector: nest under deepest open heading.
                depth = last_depth + 1
            last_depth = depth
            hits.append(
                _HeadingHit(
                    page_number=page_number,
                    line_index=index,
                    depth=depth,
                )
            )
    return hits


class SectionDetectionService:
    """Detect and store major sections for one document."""

    def __init__(self, session: Session, detector: SectionDetector | None = None):
        self.session = session
        self.detector = detector or SectionDetector()

    # ── public API ───────────────────────────────────────────────

    def run(
        self, document_id: int, *, replace: bool = True
    ) -> SectionDetectionSummary:
        document = self.session.get(Document, document_id)
        if document is None:
            raise NotFoundError("Document", document_id)

        cleaned_pages = _cleaned_pages(self.session, document_id)
        if not cleaned_pages:
            raise ValidationError(
                f"Document {document_id} has no cleaned page text to analyze"
            )

        roots = self.detector.detect(cleaned_pages)

        if replace:
            self._clear_existing(document)
        stored = self._persist(document, roots, cleaned_pages)

        unknown = sum(1 for s in stored if s.section_type == "Other")
        summary = SectionDetectionSummary(
            document_id=document_id,
            sections_stored=len(stored),
            roots=len(roots),
            unknown_headings=unknown,
            sections=stored,
        )
        logger.info(
            "section detection done document_id=%s stored=%s roots=%s unknown=%s",
            document_id,
            len(stored),
            len(roots),
            unknown,
        )
        return summary

    # ── internals ────────────────────────────────────────────────

    def _clear_existing(self, document: Document) -> None:
        """Drop previous sections so re-runs never duplicate rows."""
        _ = list(document.sections)  # force-load before clearing
        document.sections.clear()
        self.session.flush()

    def _persist(
        self,
        document: Document,
        roots: list[DetectedSection],
        cleaned_pages: dict[int, str],
    ) -> list[DocumentSection]:
        boundaries = self._compute_boundaries(roots, cleaned_pages)
        stored: list[DocumentSection] = []

        def insert(detected: DetectedSection, parent_row: DocumentSection | None):
            start_pos, end_pos = boundaries[id(detected)]
            row = DocumentSection(
                document_id=document.id,
                parent_section_id=parent_row.id if parent_row else None,
                section_title=detected.title[:512],
                section_type=detected.section_type,
                page_start=detected.page_start,
                page_end=detected.page_end,
                text=self._slice_text(cleaned_pages, start_pos, end_pos),
            )
            self.session.add(row)
            self.session.flush()  # assign id before inserting children
            stored.append(row)
            for child in detected.children:
                insert(child, row)

        for root in roots:
            insert(root, None)
        return stored

    def _compute_boundaries(
        self,
        roots: list[DetectedSection],
        cleaned_pages: dict[int, str],
    ) -> dict[int, tuple[tuple[int, int], tuple[int, int]]]:
        """Map each section's id() to (body_start, body_end) line positions.

        The body starts on the line after its heading and ends right
        before the next heading at the same-or-shallower depth (or end
        of document), so parents naturally span their children.
        Keyed by ``id()`` because DetectedSection is unhashable.
        """
        hits = _scan_heading_hits(cleaned_pages, self.detector._detect_generic)
        flat = [sec for root in roots for sec in root.flat]
        if len(hits) != len(flat):
            logger.warning(
                "heading scan mismatch (%s hits vs %s sections)", len(hits), len(flat)
            )

        # All (page, line_index) positions, document order — used to walk
        # forward/backward between heading lines.
        positions: list[tuple[int, int]] = []
        for page_number in sorted(cleaned_pages):
            positions.extend(
                (page_number, i) for i in range(len(cleaned_pages[page_number].splitlines()))
            )
        last_pos = positions[-1] if positions else (max(cleaned_pages), 0)

        boundaries: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {}
        for i, hit in enumerate(hits):
            detected = flat[i] if i < len(flat) else None
            if detected is None:
                continue
            start = self._advance(positions, (hit.page_number, hit.line_index))
            end = last_pos
            for later in hits[i + 1 :]:
                if later.depth <= hit.depth:
                    candidate = self._retreat(
                        positions, (later.page_number, later.line_index)
                    )
                    if candidate is not None:
                        end = candidate
                    break
            boundaries[id(detected)] = (start, end)
        return boundaries

    @staticmethod
    def _advance(
        positions: list[tuple[int, int]], pos: tuple[int, int]
    ) -> tuple[int, int]:
        """Smallest position strictly greater than ``pos`` (end of doc fallback)."""
        for candidate in positions:
            if candidate > pos:
                return candidate
        return pos

    @staticmethod
    def _retreat(
        positions: list[tuple[int, int]], pos: tuple[int, int]
    ) -> tuple[int, int] | None:
        """Largest position strictly less than ``pos``, skipping trailing
        blank lines; None when nothing precedes."""
        index = None
        for i, candidate in enumerate(positions):
            if candidate >= pos:
                break
            index = i
        if index is None:
            return None
        return positions[index]

    @staticmethod
    def _slice_text(
        pages: dict[int, str],
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> str:
        """Verbatim lines from ``start`` through ``end`` (originals kept)."""
        pieces: list[str] = []
        for page_number in sorted(pages):
            lines = pages[page_number].splitlines()
            for index, line in enumerate(lines):
                pos = (page_number, index)
                if pos < start or pos > end:
                    continue
                pieces.append(line)
        # Trim blank padding at both ends without touching inner content.
        while pieces and not pieces[0].strip():
            pieces.pop(0)
        while pieces and not pieces[-1].strip():
            pieces.pop()
        return "\n".join(pieces)
