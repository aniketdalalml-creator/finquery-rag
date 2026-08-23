"""Tests for the standalone DocumentChunkingService (sections → chunks)."""

from uuid import uuid4

import pytest

from app.core.errors import NotFoundError
from app.ingestion.chunking.chunker import count_tokens
from app.models.document import DocumentChunk, DocumentSection
from app.services.chunking_service import DocumentChunkingService


@pytest.fixture
def make_document(db_session, company_factory, document_factory):
    def _make(sections: list[dict]):
        company = company_factory(f"CH{uuid4().hex[:6].upper()}")
        document = document_factory(company=company, title="Chunk Target 10-K")
        for spec in sections:
            db_session.add(
                DocumentSection(document_id=document.id, **spec)
            )
        db_session.flush()
        return document

    return _make


def chunks_for(db_session, document_id: int) -> list[DocumentChunk]:
    return (
        db_session.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )


def test_chunk_size_respected(db_session, make_document):
    """Every chunk stays within the configured token budget."""
    paragraph = " ".join(
        f"Sentence number {i} adds several words to the section body."
        for i in range(40)
    )
    document = make_document(
        [
            {
                "section_title": "Business",
                "section_type": "Business",
                "page_start": 1,
                "page_end": 3,
                "text": paragraph,
            }
        ]
    )

    result = DocumentChunkingService(db_session, chunk_size=40, overlap_tokens=0).run(
        document.id
    )

    rows = chunks_for(db_session, document.id)
    assert result["chunks"] == len(rows) > 1
    assert all(row.token_count <= 40 for row in rows)
    # Reconstructing all chunk text must cover the original content.
    assert all(row.text.strip() for row in rows)


def test_overlap_carries_sentences_between_chunks(db_session, make_document):
    """With overlap > 0 consecutive chunks share their boundary sentences."""
    sentences = [
        f"Sentence {i} discusses operating results in detail." for i in range(30)
    ]
    document = make_document(
        [
            {
                "section_title": "MD&A",
                "section_type": "MD&A",
                "page_start": 4,
                "page_end": 6,
                "text": " ".join(sentences),
            }
        ]
    )

    DocumentChunkingService(db_session, chunk_size=45, overlap_tokens=12).run(
        document.id
    )

    rows = chunks_for(db_session, document.id)
    assert len(rows) >= 2

    def pieces(text: str) -> set[str]:
        # Normalize: only the final sentence keeps a trailing period.
        return {p.strip().rstrip(".") for p in text.split(". ") if p.strip()}

    for prev, nxt in zip(rows, rows[1:]):
        shared = pieces(prev.text) & pieces(nxt.text)
        assert shared, "no overlap between consecutive chunks"
        # Overlap must be a tail of the previous chunk and head of the next.
        assert any(nxt.text.startswith(s) for s in shared)


def test_provenance_section_pages_and_metadata(db_session, make_document):
    """Chunks keep section_id, the section's page span and metadata."""
    document = make_document(
        [
            {
                "section_title": "Risk Factors",
                "section_type": "Risk Factors",
                "page_start": 7,
                "page_end": 9,
                "text": "Credit risk exists. Market risk also exists. Liquidity matters.",
            }
        ]
    )
    section = (
        db_session.query(DocumentSection)
        .filter(DocumentSection.document_id == document.id)
        .one()
    )

    DocumentChunkingService(db_session).run(document.id)

    rows = chunks_for(db_session, document.id)
    assert len(rows) == 1
    row = rows[0]
    assert row.section_id == section.id
    assert row.page_start == 7
    assert row.page_end == 9
    assert row.chunk_type == "text"
    assert row.chunk_metadata["section_title"] == "Risk Factors"
    assert row.chunk_metadata["section_type"] == "Risk Factors"
    assert row.chunk_metadata["section_path"] == ["Risk Factors"]
    assert row.token_count == count_tokens(row.text)


def test_empty_text_sections_produce_no_chunks(db_session, make_document):
    """None / blank section text is skipped; originals stay untouched."""
    document = make_document(
        [
            {
                "section_title": "Empty",
                "section_type": "Other",
                "page_start": 1,
                "page_end": 1,
                "text": None,
            },
            {
                "section_title": "Blank",
                "section_type": "Other",
                "page_start": 2,
                "page_end": 2,
                "text": "   \n  ",
            },
            {
                "section_title": "Real",
                "section_type": "Other",
                "page_start": 3,
                "page_end": 3,
                "text": "Only this section has words.",
            },
        ]
    )
    before = {
        s.section_title: s.text
        for s in db_session.query(DocumentSection)
        .filter(DocumentSection.document_id == document.id)
        .all()
    }

    result = DocumentChunkingService(db_session).run(document.id)

    rows = chunks_for(db_session, document.id)
    assert result["sections"] == 3
    assert result["sections_chunked"] == 1
    assert len(rows) == 1
    assert rows[0].chunk_metadata["section_title"] == "Real"
    # Original section text untouched.
    after = {
        s.section_title: s.text
        for s in db_session.query(DocumentSection)
        .filter(DocumentSection.document_id == document.id)
        .all()
    }
    assert after == before
    # A fully empty document yields zero chunks.
    empty_doc = make_document(
        [{"section_title": "N", "section_type": "Other", "text": None}]
    )
    empty_result = DocumentChunkingService(db_session).run(empty_doc.id)
    assert empty_result["chunks"] == 0


def test_multiple_sections_order_rerun_replaces(db_session, make_document):
    """Sections are chunked in page order with global indices; rerun replaces."""
    document = make_document(
        [
            {
                "section_title": "Second",
                "section_type": "Other",
                "page_start": 10,
                "page_end": 12,
                "text": "Beta section body sentence one. Beta section body sentence two.",
            },
            {
                "section_title": "First",
                "section_type": "Other",
                "page_start": 2,
                "page_end": 4,
                "text": "Alpha section body sentence one. Alpha section body sentence two.",
            },
        ]
    )

    first = DocumentChunkingService(db_session).run(document.id)
    rows = chunks_for(db_session, document.id)
    titles_in_order = [r.chunk_metadata["section_title"] for r in rows]
    assert titles_in_order == sorted(titles_in_order, key=lambda t: ["First", "Second"].index(t))
    assert [r.chunk_index for r in rows] == list(range(first["chunks"]))
    assert {r.section_id for r in rows} != {None}

    # Rerun replaces instead of duplicating.
    second = DocumentChunkingService(db_session).run(document.id)
    rows_after = chunks_for(db_session, document.id)
    assert second["chunks"] == first["chunks"]
    assert len(rows_after) == len(rows)
    assert [r.text for r in rows_after] == [r.text for r in rows]


def test_unknown_document_raises(db_session):
    with pytest.raises(NotFoundError):
        DocumentChunkingService(db_session).run(document_id=99999)


def test_invalid_parameters_rejected(db_session, make_document):
    document = make_document([])
    with pytest.raises(ValueError):
        DocumentChunkingService(db_session, chunk_size=0)
    with pytest.raises(ValueError):
        DocumentChunkingService(db_session, chunk_size=10, overlap_tokens=10)
