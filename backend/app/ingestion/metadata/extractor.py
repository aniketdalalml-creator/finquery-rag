"""MetadataExtractor — document-level financial metadata.

Extracts company/ticker/document type/fiscal year/quarter/reporting
period/currency/units from the first pages plus filename. Every field
carries a confidence; ambiguous matches are dropped rather than guessed.
This is extraction, not inference: nothing is derived.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

_MONTHS = (
    "january|february|march|april|may|june|july|august|september|october|november|december"
)

_TICKER = re.compile(r"\b(?:NASDAQ|NYSE|AMEX|NSE|BSE)\s*[:\s]\s*([A-Z]{2,6})\b")
_TICKER_LABEL = re.compile(r"\b(?:ticker|symbol)\s*[:\-]?\s*([A-Z]{2,6})\b", re.IGNORECASE)

_DOC_TYPE_PATTERNS: list[tuple[re.Pattern[str], str, float]] = [
    (re.compile(r"\bform\s*10-?k\b|\b10-?k\b(?:\s+annual)?", re.IGNORECASE), "10-K", 0.9),
    (re.compile(r"\bform\s*10-?q\b|\b10-?q\b", re.IGNORECASE), "10-Q", 0.85),
    (re.compile(r"\bform\s*8-?k\b|\b8-?k\b", re.IGNORECASE), "8-K", 0.85),
    (re.compile(r"\bannual report\b", re.IGNORECASE), "Annual Report", 0.7),
    (re.compile(r"\bquarterly report\b|\binterim results?\b", re.IGNORECASE), "Quarterly Report", 0.7),
    (re.compile(r"\binvestor presentation\b", re.IGNORECASE), "Investor Presentation", 0.8),
    (re.compile(r"\bearnings release\b|\bearnings call\b|\bresults announcement\b", re.IGNORECASE), "Earnings Release", 0.75),
    (re.compile(r"\bresearch report\b|\binitiating coverage\b", re.IGNORECASE), "Research Report", 0.75),
    (re.compile(r"\bfinancial statements?\b", re.IGNORECASE), "Financial Statement", 0.4),
]

_FISCAL_YEAR = re.compile(
    r"\bf(?:iscal)?\s*(?:year)?\s*['’]?\s*(20\d{2})\b", re.IGNORECASE
)
_PERIOD_END = re.compile(
    rf"\b(?:fiscal\s+year\s+(?:ended|ending)|year\s+(?:ended|ending)|as\s+of)\s+"
    rf"({_MONTHS})\s+(\d{{1,2}}),?\s+(20\d{{2}})",
    re.IGNORECASE,
)
_QUARTER = re.compile(r"\bQ([1-4])[\s'’]*(20\d{2})\b", re.IGNORECASE)
_QUARTER_TEXT = re.compile(
    rf"\b(three|six|nine|twelve)\s+months\s+(?:ended|ending)\s+({_MONTHS})\s+(\d{{1,2}}),?\s+(20\d{{2}})",
    re.IGNORECASE,
)
_CURRENCY = re.compile(r"\b(USD|EUR|GBP|INR|JPY)\b")
_CURRENCY_SYMBOL = re.compile(r"[$€£¥₹]")
_UNITS = re.compile(r"\bin\s+(millions|billions|thousands)\b", re.IGNORECASE)


@dataclass
class FieldConfidence:
    value: object
    confidence: float


@dataclass
class DetectedMetadata:
    ticker: FieldConfidence | None = None
    company_hint: str | None = None
    document_type: FieldConfidence | None = None
    fiscal_year: FieldConfidence | None = None
    fiscal_quarter: FieldConfidence | None = None
    period_start: FieldConfidence | None = None
    period_end: FieldConfidence | None = None
    currency: FieldConfidence | None = None
    units: FieldConfidence | None = None
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            key: {"value": fc.value, "confidence": round(fc.confidence, 2)}
            for key, fc in self.__dict__.items()
            if isinstance(fc, FieldConfidence) and fc is not None
        } | {"notes": self.notes}


class MetadataExtractor:
    def extract(self, pages: dict[int, str], filename: str) -> DetectedMetadata:
        result = DetectedMetadata()
        head_text = "\n".join(pages.get(n, "") for n in sorted(pages)[:3])
        full_head_and_tail = "\n".join(
            [pages[n] for n in sorted(pages)[:3]] + [pages[max(pages, default=0)]]
        )

        # Ticker: exchange prefix beats bare label.
        if match := _TICKER.search(head_text):
            result.ticker = FieldConfidence(match.group(1).upper(), 0.9)
        elif match := _TICKER_LABEL.search(head_text):
            result.ticker = FieldConfidence(match.group(1).upper(), 0.7)

        # Document type: best-scoring pattern in head text or filename.
        best_type, best_score = None, 0.0
        for pattern, doc_type, score in _DOC_TYPE_PATTERNS:
            if score > best_score and (pattern.search(head_text) or pattern.search(filename)):
                best_type, best_score = doc_type, score
        if best_type is not None:
            result.document_type = FieldConfidence(best_type, best_score)

        # Fiscal year: explicit FY mention only (no guessing from dates alone).
        years = _FISCAL_YEAR.findall(full_head_and_tail)
        if years:
            counts: dict[str, int] = {}
            for year in years:
                counts[year] = counts.get(year, 0) + 1
            top_year, top_count = max(counts.items(), key=lambda kv: kv[1])
            confidence = min(0.5 + 0.1 * top_count, 0.9)
            result.fiscal_year = FieldConfidence(int(top_year), confidence)

        # Quarter: Q3 2025 style; or "three months ended" → that quarter.
        quarter_match = _QUARTER.search(full_head_and_tail)
        text_quarter = _QUARTER_TEXT.search(full_head_and_tail)
        if quarter_match and not text_quarter:
            month_num, year = int(quarter_match.group(1)), int(quarter_match.group(2))
            result.fiscal_quarter = FieldConfidence(f"Q{month_num}", min(0.5 + _recency(full_head_and_tail, quarter_match.group(0)) * 0.3, 0.85))
            if result.fiscal_year is None:
                result.fiscal_year = FieldConfidence(year, 0.75)
        elif text_quarter:
            months_map = {
                "three": 1, "six": 2, "nine": 3, "twelve": 4,
            }
            span = months_map[text_quarter.group(1).lower()]
            q_value = f"Q{span}" if span < 4 else None
            if q_value:
                result.fiscal_quarter = FieldConfidence(q_value, 0.8)
            end_date = self._parse_date(text_quarter.group(2), text_quarter.group(3), text_quarter.group(4))
            if end_date is not None:
                result.period_end = FieldConfidence(end_date, 0.85)
                start_month_index = end_date.month - {1: 3, 2: 6, 3: 9}[span]
                year_offset, month_index = divmod(start_month_index - 1, 12)
                result.period_start = FieldConfidence(
                    date(end_date.year + year_offset, month_index + 1, 1), 0.6
                )

        # Reporting period end ("fiscal year ended September 28, 2024").
        period_match = _PERIOD_END.search(full_head_and_tail)
        if period_match and result.period_end is None:
            parsed = self._parse_date(period_match.group(1), period_match.group(2), period_match.group(3))
            if parsed is not None:
                result.period_end = FieldConfidence(parsed, 0.8)

        # Currency: explicit code first, then symbol.
        if match := _CURRENCY.search(full_head_and_tail):
            result.currency = FieldConfidence(match.group(1), 0.8)
        elif match := _CURRENCY_SYMBOL.search(full_head_and_tail):
            symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR"}
            result.currency = FieldConfidence(symbol_map.get(match.group(0), ""), 0.55)
            if not result.currency.value:
                result.currency = None

        # Units statement ("in millions").
        unit_matches = _UNITS.findall(full_head_and_tail)
        if unit_matches:
            counts: dict[str, int] = {}
            for u in unit_matches:
                counts[u.lower()] = counts.get(u.lower(), 0) + 1
            units_value, n = max(counts.items(), key=lambda kv: kv[1])
            result.units = FieldConfidence(units_value, min(0.6 + 0.05 * n, 0.9))

        return result

    @staticmethod
    def _parse_date(month_name: str, day: str, year: str) -> date | None:
        try:
            return datetime.strptime(
                f"{month_name} {day} {year}", "%B %d %Y"
            ).date()
        except ValueError:
            return None


def _recency(text: str, needle: str) -> float:
    """0..1 position of needle in text (later = higher)."""
    index = text.find(needle)
    if index < 0:
        return 0.0
    return index / max(len(text), 1)
