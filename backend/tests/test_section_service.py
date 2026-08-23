"""Tests for the standalone SectionDetectionService.

Covers: known-heading detection, page-range assignment, unknown
headings, and parent/child nesting — against a scratch SQLite DB
(never the production MySQL database).
"""

from __future__ import annotations

import pytest

from app.core.errors import NotFoundError, ValidationError
from app.services.section_detection_service import SectionDetectionService


def _add_pages(db_session, document, pages: dict[int, str]):
    from app.models.document import DocumentPage

    for number, text in pages.items():
        db_session.add(
            DocumentPage(
                document_id=document.id,
                page_number=number,
                raw_text=text,
                cleaned_text=text,
            )
        )
    db_session.flush()


# ── 1. detecting headings ────────────────────────────────────────────


def test_detects_known_headings(db_session, document_factory):
    document = document_factory()
    _add_pages(
        db_session,
        document,
        {
            1: (
                "Business Overview\n\n"
                "We design smartphones and services.\n\n"
                "Risk Factors\n\n"
                "Tariffs may hurt our margins.\n"
            ),
            2: "Income Statement\n\nNet sales grew five percent year over year.\n",
        },
    )

    summary = SectionDetectionService(db_session).run(document.id)

    assert summary.sections_stored == 3
    assert summary.unknown_headings == 0
    by_title = {s.section_title: s for s in summary.sections}
    assert set(by_title) == {"Business Overview", "Risk Factors", "Income Statement"}
    assert by_title["Business Overview"].section_type == "Business Overview"
    assert by_title["Risk Factors"].section_type == "Risk Factors"
    assert by_title["Income Statement"].section_type == "Income Statement"


# ── 2. assigning page ranges ─────────────────────────────────────────


def test_assigns_page_ranges(db_session, document_factory):
    document = document_factory()
    _add_pages(
        db_session,
        document,
        {
            1: "Introductory boilerplate with no headings at all.\n",
            2: "Financial Statements\n\nThe statements follow this page.\n",
            3: "More statement detail continues on this page.\n",
            4: "Notes to Financial Statements\n\nAccounting policies apply.\n",
        },
    )

    summary = SectionDetectionService(db_session).run(document.id)

    by_title = {s.section_title: s for s in summary.sections}
    financial = by_title["Financial Statements"]
    notes = by_title["Notes to Financial Statements"]
    # Starts on its heading page; runs through the page where the next
    # heading begins (sections may share that boundary page).
    assert (financial.page_start, financial.page_end) == (2, 4)
    assert (notes.page_start, notes.page_end) == (4, 4)


# ── 3. handling unknown headings ─────────────────────────────────────


def test_unknown_headings_kept_as_other_with_verbatim_text(
    db_session, document_factory
):
    document = document_factory()
    body_line = "Component lead times doubled during the year."
    _add_pages(
        db_session,
        document,
        {
            1: f"Supply Chain Overview\n\n{body_line}\n",
            2: "Risk Factors\n\nTariffs and trade restrictions apply.\n",
        },
    )

    summary = SectionDetectionService(db_session).run(document.id)

    assert summary.sections_stored == 2
    assert summary.unknown_headings == 1
    section = summary.sections[0]
    assert section.section_title == "Supply Chain Overview"
    assert section.section_type == "Other"
    assert section.text == body_line  # original text preserved exactly


def test_document_without_headings_yields_no_sections(db_session, document_factory):
    document = document_factory()
    _add_pages(db_session, document, {1: "Just paragraphs of plain prose.\nNo titles.\n"})

    summary = SectionDetectionService(db_session).run(document.id)

    assert summary.sections_stored == 0
    assert summary.sections == []


# ── 4. basic parent/child sections ───────────────────────────────────


def test_parent_child_sections_nest_and_span(db_session, document_factory):
    document = document_factory()
    _add_pages(
        db_session,
        document,
        {
            1: (
                "Financial Statements\n\n"
                "This overview introduces the statements.\n\n"
                "Income Statement\n\n"
                "Revenues rose steadily.\n\n"
                "Balance Sheet\n\n"
                "Assets equal liabilities plus equity.\n"
            ),
        },
    )
    service = SectionDetectionService(db_session)

    summary = service.run(document.id)

    by_title = {s.section_title: s for s in summary.sections}
    parent = by_title["Financial Statements"]
    income = by_title["Income Statement"]
    balance = by_title["Balance Sheet"]

    assert income.parent_section_id == parent.id
    assert balance.parent_section_id == income.id  # detector chains nested items
    assert parent.parent_section_id is None

    # Parent spans everything below it; chained children contain theirs.
    assert parent.text.startswith("This overview introduces")
    assert "Assets equal liabilities plus equity." in parent.text
    assert income.text.startswith("Revenues rose steadily.")
    assert "Balance Sheet" in income.text  # nested section stays inside parent body
    assert balance.text == "Assets equal liabilities plus equity."
    assert balance.page_start == parent.page_start == 1

    # Re-running replaces instead of duplicating.
    again = service.run(document.id)
    assert again.sections_stored == summary.sections_stored


# ── guard rails ──────────────────────────────────────────────────────


def test_missing_document_raises(db_session):
    with pytest.raises(NotFoundError):
        SectionDetectionService(db_session).run(999999)


def test_document_without_cleaned_pages_raises(db_session, document_factory):
    document = document_factory()
    with pytest.raises(ValidationError):
        SectionDetectionService(db_session).run(document.id)
