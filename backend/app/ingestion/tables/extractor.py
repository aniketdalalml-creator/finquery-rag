"""TableExtractor — detects columnar tables in cleaned page text.

Financial PDFs rarely carry real table markup, so this is a conservative
text-heuristics extractor:

- a table is a run of >= 3 consecutive lines that split into the same
  number of columns (2+ spaces or pipe separators)
- the line above the block becomes the title when it looks like a caption
- confidence reflects column-count stability and numeric-cell density
- when parsing is unreliable, the raw block is kept with low confidence
  and no invented cells

Pipe-delimited blocks (HTML/markdown exports) parse first; whitespace
alignment is used otherwise.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

_MIN_LINES = 3
_COLUMN_GAP = re.compile(r"\s{2,}|\t+|\s*\|\s*")
_LEADING_PIPE = re.compile(r"^\s*\|(.*)\|\s*$")
_NUMERIC = re.compile(
    r"^[$€£¥]?\(?-?[\d.,]+\)?%?$"  # 1,234.56 / (500) / $12 / 45%
)
_UNIT_HINT = re.compile(r"\b(in\s+(?:millions|billions|thousands)|usd\s*(millions|billions)?)\b", re.IGNORECASE)
_CURRENCY_HINT = re.compile(r"\b(USD|EUR|GBP|INR|JPY)\b|[$€£¥₹]")
_YEAR_LIKE = re.compile(r"^(19|20)\d{2}[a-z]?$", re.IGNORECASE)


@dataclass
class DetectedTable:
    page_number: int
    headers: list[str]
    rows: list[list[str]]
    title: str | None = None
    units: str | None = None
    currency: str | None = None
    confidence: Decimal = Decimal("0.0")
    raw_text: str = ""
    extraction_ok: bool = True
    notes: list[str] = field(default_factory=list)


def _split_columns(line: str) -> list[str]:
    pipe_match = _LEADING_PIPE.match(line)
    if pipe_match:
        return [cell.strip() for cell in pipe_match.group(1).split("|")]
    parts = [p.strip() for p in _COLUMN_GAP.split(line.strip()) if p.strip()]
    return parts if len(parts) > 1 else ([line.strip()] if line.strip() else [])


def _is_numeric_cell(cell: str) -> bool:
    return bool(_NUMERIC.match(cell.replace(",", "")))


class TableExtractor:
    def __init__(self, min_table_lines: int = _MIN_LINES) -> None:
        self._min_lines = min_table_lines

    def extract_from_page(self, page_number: int, text: str) -> list[DetectedTable]:
        lines = text.splitlines()
        tables: list[DetectedTable] = []
        index = 0
        while index < len(lines):
            block = self._collect_block(lines, index)
            if block is None:
                index += 1
                continue
            start, end = block
            raw_block = "\n".join(lines[start:end])
            table = self._parse_block(page_number, raw_block, lines[start - 1] if start > 0 else "")
            if table is not None:
                tables.append(table)
            index = end
        return tables

    def _collect_block(self, lines: list[str], start: int) -> tuple[int, int] | None:
        """Return (start, end) of a multi-column run starting at `start`."""
        first_cols = len(_split_columns(lines[start]))
        if first_cols < 2:
            return None
        end = start + 1
        widths = {first_cols}
        while end < len(lines):
            cols = len(_split_columns(lines[end]))
            if cols < 2:
                break
            widths.add(cols)
            # Column-count drift of more than one suggests a new block.
            if max(widths) - min(widths) > 1 and len(widths) > 2:
                break
            end += 1
        if end - start < self._min_lines:
            return None
        return start, end

    def _parse_block(
        self, page_number: int, raw_block: str, preceding_line: str
    ) -> DetectedTable | None:
        rows = [_split_columns(line) for line in raw_block.splitlines() if line.strip()]
        if not rows:
            return None

        width_counts: dict[int, int] = {}
        for row in rows:
            width_counts[len(row)] = width_counts.get(len(row), 0) + 1
        dominant_width = max(width_counts, key=width_counts.get)

        title = self._title_from(preceding_line)
        units, currency = self._units_currency(raw_block)

        stable_rows = [row for row in rows if len(row) == dominant_width]
        unstable = len(rows) - len(stable_rows)

        header_row = self._header_row(stable_rows)
        body = stable_rows[1:] if header_row is not None else stable_rows

        numeric_ratio = (
            sum(
                1
                for row in body
                for cell in row[1:] if _is_numeric_cell(cell)
            )
            / max(1, sum(len(row[1:]) for row in body))
        )

        confidence = Decimal("0.50")
        confidence += Decimal("0.15") if header_row is not None else Decimal("0.00")
        confidence += Decimal("0.25") * Decimal(str(round(numeric_ratio, 2)))
        if unstable:
            confidence -= Decimal("0.10") * min(unstable, 3)
        confidence = max(Decimal("0.05"), min(confidence, Decimal("0.98")))

        extraction_ok = len(body) >= 2 and (unstable == 0 or confidence >= Decimal("0.55"))
        notes: list[str] = []
        if not extraction_ok:
            notes.append("unreliable structure; keeping raw text with low confidence")

        return DetectedTable(
            page_number=page_number,
            headers=[c for c in (header_row or [])],
            rows=[[c for c in row] for row in (body if extraction_ok else [])],
            title=title,
            units=units,
            currency=currency,
            confidence=confidence.quantize(Decimal("0.01")),
            raw_text=raw_block,
            extraction_ok=extraction_ok,
            notes=notes,
        )

    @staticmethod
    def _title_from(preceding_line: str) -> str | None:
        candidate = preceding_line.strip().rstrip(":").strip()
        if not candidate or len(candidate) > 200:
            return None
        if _UNIT_HINT.search(candidate) or _YEAR_LIKE.match(candidate):
            return candidate or None
        words = candidate.split()
        if 2 <= len(words) <= 20:
            return candidate
        return None

    @staticmethod
    def _units_currency(block_text: str) -> tuple[str | None, str | None]:
        units = None
        currency = None
        unit_match = _UNIT_HINT.search(block_text)
        if unit_match:
            phrase = unit_match.group(0).lower()
            units = "millions" if "million" in phrase else "billions" if "billion" in phrase else "thousands"
        currency_match = _CURRENCY_HINT.search(block_text)
        if currency_match:
            symbol = currency_match.group(0)
            mapping = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR"}
            currency = mapping.get(symbol, symbol.upper())
        return units, currency

    @staticmethod
    def _header_row(rows: list[list[str]]) -> list[str] | None:
        if not rows:
            return None
        candidate = rows[0]
        has_year = any(_YEAR_LIKE.match(cell) for cell in candidate)
        has_no_numbers = not any(_is_numeric_cell(cell.replace(",", "")) for cell in candidate[1:])
        if has_year or (has_no_numbers and len(candidate) >= 2):
            return candidate
        return None
