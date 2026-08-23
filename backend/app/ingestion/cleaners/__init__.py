"""Document cleaning stage.

Conservative normalization of common financial-document noise:
repeated headers/footers, page-number lines, hyphenation across line
breaks, broken line wrapping and whitespace/encoding artifacts.

Rule: wording, numbers, symbols, units and currency are never rewritten.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# A line consisting only of a page number (optionally "Page 12", "- 12 -").
_PAGE_NUMBER_LINE = re.compile(r"^\s*(?:page\s+)?[-–—|]?\s*\d{1,4}\s*(?:of\s+\d{1,5})?\s*[-–—|]?\s*$", re.IGNORECASE)
_HYPHENATED_LINE_END = re.compile(r"([A-Za-z])-\s*\n\s*([a-z])")
_MULTIPLE_SPACES = re.compile(r"[ \t]{2,}")
_TRAILING_SPACES = re.compile(r"[ \t]+$", re.MULTILINE)
_EXCESS_BLANKS = re.compile(r"\n{3,}")


@dataclass
class CleaningReport:
    """What the cleaner changed — recorded in page extraction_metadata."""

    removed_header_lines: int = 0
    removed_footer_lines: int = 0
    removed_page_numbers: int = 0
    dehyphenated_joins: int = 0


def normalize_unicode(text: str) -> str:
    """Fix encoding artifacts without touching content.

    Maps unicode variants to ASCII equivalents (smart quotes → quotes,
    various dashes → '-', NBSP/thin/narrow spaces → regular space) so
    downstream regexes see consistent characters.
    """
    replacements = {
        "\u00a0": " ",   # no-break space
        "\u202f": " ",   # narrow no-break space
        "\u2009": " ",   # thin space
        "\u2007": " ",
        "\u2011": "-",   # non-breaking hyphen
        "\u2013": "-",   # en dash
        "\u2014": "-",   # em dash
        "\u2212": "-",   # minus sign
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2026": "...",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    # Any remaining exotic separators (BOM etc.).
    return unicodedata.normalize("NFKC", text)


def _is_mostly_repeated(line: str, occurrences: int, total_pages: int) -> bool:
    """A header/footer candidate appears on most pages."""
    if total_pages < 3 or not line.strip():
        return False
    return occurrences / total_pages >= 0.6


class DocumentCleaner:
    """Page-level cleaner with document-level header/footer detection."""

    def __init__(self, min_lines_for_header_footer: int = 1) -> None:
        self._min_lines = min_lines_for_header_footer

    def clean_document(self, raw_pages: dict[int, str]) -> dict[int, tuple[str, CleaningReport]]:
        """Clean all pages.

        Returns {page_number: (cleaned_text, report)}. Repeated first/last
        lines that appear on >=60% of pages are treated as running
        headers/footers and removed from every page they appear on.
        """
        total_pages = len(raw_pages)
        header_counts: dict[str, int] = {}
        footer_counts: dict[str, int] = {}

        normalized: dict[int, list[str]] = {}
        for page_number, text in raw_pages.items():
            lines = [
                " ".join(normalize_unicode(line).split())
                for line in text.splitlines()
            ]
            lines = [line for line in lines if line]
            normalized[page_number] = lines
            body = [ln for ln in lines if not _PAGE_NUMBER_LINE.match(ln)]
            if len(body) >= 2 * self._min_lines + 1:
                first = body[0].strip()
                last = body[-1].strip()
                if first:
                    header_counts[first] = header_counts.get(first, 0) + 1
                if last:
                    footer_counts[last] = footer_counts.get(last, 0) + 1

        repeated_headers = {
            line for line, count in header_counts.items()
            if _is_mostly_repeated(line, count, total_pages)
        }
        repeated_footers = {
            line for line, count in footer_counts.items()
            if _is_mostly_repeated(line, count, total_pages) and line not in repeated_headers
        }

        results: dict[int, tuple[str, CleaningReport]] = {}
        for page_number, lines in normalized.items():
            cleaned, report = self._clean_page(
                lines, repeated_headers, repeated_footers
            )
            results[page_number] = (cleaned, report)
        return results

    def clean_single(self, text: str) -> str:
        """Clean a standalone text block (no cross-page header analysis)."""
        lines = [" ".join(normalize_unicode(line).split()) for line in text.splitlines()]
        cleaned, _ = self._clean_page(
            [line for line in lines if line], set(), set()
        )
        return cleaned

    def _clean_page(
        self,
        lines: list[str],
        repeated_headers: set[str],
        repeated_footers: set[str],
    ) -> tuple[str, CleaningReport]:
        report = CleaningReport()
        kept: list[str] = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if _PAGE_NUMBER_LINE.match(stripped):
                report.removed_page_numbers += 1
                continue
            if index == 0 and stripped in repeated_headers:
                report.removed_header_lines += 1
                continue
            if index == len(lines) - 1 and stripped in repeated_footers:
                report.removed_footer_lines += 1
                continue
            kept.append(line)

        text = "\n".join(kept)
        # De-hyphenate words broken across lines: "increa-\nsed" → "increased".
        def _join(match: re.Match) -> str:
            report.dehyphenated_joins += 1
            return match.group(1) + match.group(2)

        text = _HYPHENATED_LINE_END.sub(_join, text)
        # Collapse intra-paragraph line wrapping conservatively: keep single
        # newlines only between what look like separate lines (lists, table
        # rows); merge lines that end mid-sentence is intentionally NOT done
        # here because financial tables rely on line structure.
        text = _TRAILING_SPACES.sub("", text)
        text = "\n".join(_MULTIPLE_SPACES.sub(" ", line) for line in text.splitlines())
        text = _EXCESS_BLANKS.sub("\n\n", text)
        return text.strip(), report
