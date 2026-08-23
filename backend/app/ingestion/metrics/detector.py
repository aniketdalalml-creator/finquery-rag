"""MetricDetector — finds metric mentions with values and periods.

Extraction only: no derived metrics, no financial reasoning. A detection
must bind a known metric name to a concrete value in the same line;
otherwise it is discarded. Confidence reflects pattern strength and
context (period presence raises it).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.services.metric_service import normalize_metric_name

# canonical name → synonyms (matched case-insensitively as label before a value)
_METRIC_SYNONYMS: list[tuple[str, str, str]] = [
    # canonical, regex-alternation, metric_type
    ("revenue", r"(?:total\s+)?(?:net\s+)?(?:revenues?|net\s+sales|total\s+net\s+sales|sales)", "income_statement"),
    ("gross_profit", r"gross\s+(?:profit|margin\b(?!\s*\())", "income_statement"),
    ("operating_income", r"operating\s+(?:income|profit)", "income_statement"),
    ("net_income", r"net\s+(?:income|earnings?|profit)(?:\s+after\s+taxes?)?", "income_statement"),
    ("ebitda", r"ebitda", "income_statement"),
    ("eps_basic", r"(?:basic\s+)?(?:earnings|income)\s+per\s+share", "per_share"),
    ("eps_diluted", r"diluted\s+(?:earnings|income)\s+per\s+share", "per_share"),
    ("free_cash_flow", r"free\s+cash\s+flow", "cash_flow"),
    ("total_assets", r"total\s+assets", "balance_sheet"),
    ("total_liabilities", r"total\s+liabilities", "balance_sheet"),
    ("total_debt", r"total\s+(?:debt|borrowings?|liabilies)", "balance_sheet"),
    ("cash_and_equivalents", r"cash\s+and\s+cash\s+equivalents", "balance_sheet"),
    ("operating_margin", r"operating\s+margin", "margin"),
    ("gross_margin", r"gross\s+margin", "margin"),
    ("rd_expense", r"(?:research\s+and\s+development|r&d)\s+(?:expenses?|costs?)", "income_statement"),
]

_VALUE = re.compile(
    r"""
    (?P<currency>[$€£¥₹]|USD|EUR|GBP|INR|JPY)?
    \s*
    \(?(?P<value>-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?)\)?\s*
    (?P<percent>%)?
    """,
    re.VERBOSE,
)

# Value followed by an explicit scale word (million/billion/mn/bn/k).
_SCALE = re.compile(
    r"\b(millions?|billions?|thousands?|mn|bn|k)\b",
    re.IGNORECASE,
)

_PERIOD_FY = re.compile(r"\b(?:fiscal\s*year|fy)\s*['’]?\s*(20\d{2})", re.IGNORECASE)
_PERIOD_Q = re.compile(r"\bQ([1-4])[\s'’]*(20\d{2})\b|\b(20\d{2})\s*Q([1-4])\b", re.IGNORECASE)


@dataclass
class DetectedMetric:
    raw_label: str
    canonical_name: str
    normalized_metric_name: str
    metric_type: str
    value: Decimal | None
    percent: bool
    scale_word: str | None          # millions / billions / thousands / None
    currency_symbol: str | None     # $ € £ ¥ ₹ USD EUR ...
    period_hint: str | None         # "FY2024" / "Q4 2025" style hint if present
    page_number: int
    chunk_index: int | None = None
    confidence: Decimal = Decimal("0.0")

    def resolved_value(self) -> Decimal | None:
        """Value × scale multiplier; percentages stay unscaled."""
        if self.value is None:
            return None
        if self.percent:
            return self.value
        multiplier = {
            "billion": Decimal("1e9"), "billions": Decimal("1e9"), "bn": Decimal("1e9"),
            "million": Decimal("1e6"), "millions": Decimal("1e6"), "mn": Decimal("1e6"),
            "thousand": Decimal("1e3"), "thousands": Decimal("1e3"), "k": Decimal("1e3"),
        }.get(self.scale_word or "", Decimal("1"))
        return (self.value * multiplier).normalize()


class MetricDetector:
    """Scans text chunks for `label ... value` occurrences."""

    def __init__(self) -> None:
        self._compiled = [
            (
                re.compile(
                    rf"\b({alternation})\b[^:\n%$€£¥0-9]{{0,40}}",
                    re.IGNORECASE,
                ),
                canonical,
                metric_type,
            )
            for canonical, alternation, metric_type in _METRIC_SYNONYMS
        ]
        self._scale = _SCALE
        self._period_fy = _PERIOD_FY
        self._period_q = _PERIOD_Q

    def detect_in_text(self, text: str, page_number: int, chunk_index: int | None = None) -> list[DetectedMetric]:
        found: list[DetectedMetric] = []
        seen_lines: set[tuple[str, str]] = set()
        for line in text.splitlines():
            for label_re, canonical, metric_type in self._compiled:
                match = label_re.search(line)
                if not match:
                    continue
                rest = line[match.end():][:80]
                value_match = _VALUE.search(rest)
                if not value_match:
                    continue

                key = (line.strip()[:60], canonical)
                if key in seen_lines:
                    break  # one detection per metric per line
                seen_lines.add(key)

                try:
                    number = Decimal(value_match.group("value").replace(",", ""))
                except InvalidOperation:
                    continue

                percent = bool(value_match.group("percent"))
                scale_match = self._scale.search(rest[value_match.end():][:24])
                scale_word = scale_match.group(1).lower() if scale_match else None
                # Percentages never carry scale words.
                if percent:
                    scale_word = None
                    # Reject "% of revenue"-style fragments without numbers.
                    if number == 0 and "of" in rest:
                        continue

                confidence = Decimal("0.55")
                if scale_match or percent:
                    confidence += Decimal("0.15")
                if value_match.group("currency"):
                    confidence += Decimal("0.10")
                period_hint = self._period_after(line, match.end())
                if period_hint:
                    confidence += Decimal("0.10")
                confidence = min(confidence, Decimal("0.95"))

                found.append(
                    DetectedMetric(
                        raw_label=match.group(1),
                        canonical_name=canonical,
                        normalized_metric_name=canonical,
                        metric_type=metric_type,
                        value=number,
                        percent=percent,
                        scale_word=scale_word,
                        currency_symbol=value_match.group("currency"),
                        period_hint=period_hint,
                        page_number=page_number,
                        chunk_index=chunk_index,
                        confidence=confidence.quantize(Decimal("0.01")),
                    )
                )
                break  # first matching metric per line wins
        return found

    def detect_in_chunks(self, chunks: list[dict]) -> list[DetectedMetric]:
        """chunks: [{"index": int, "text": str, "pages": [int, ...]}]."""
        out: list[DetectedMetric] = []
        for chunk in chunks:
            page_number = min(chunk.get("pages") or [0])
            out.extend(
                self.detect_in_text(chunk["text"], page_number, chunk["index"])
            )
        return out

    @staticmethod
    def _period_after(line: str, from_index: int) -> str | None:
        tail = line[from_index:from_index + 120]
        if m := _PERIOD_FY.search(tail):
            return f"FY{m.group(1)}"
        if m := _PERIOD_Q.search(tail):
            return f"Q{m.group(1) or m.group(4)} {m.group(2) or m.group(3)}"
        return None


def parse_currency(symbol: str | None, document_default: str | None = None) -> str | None:
    if symbol is None:
        return document_default
    mapping = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR"}
    upper = symbol.upper()
    if upper in {"USD", "EUR", "GBP", "INR", "JPY"}:
        return upper
    mapped = mapping.get(symbol)
    if mapped is not None:
        return mapped
    return document_default
