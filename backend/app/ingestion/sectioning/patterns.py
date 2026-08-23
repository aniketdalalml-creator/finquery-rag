"""Heading patterns for financial report sections.

Each entry maps a compiled heading regex to (canonical_title, section_type).
Types are validated against app.core.constants.SECTION_TYPES at import time.
Order matters: first match wins, so specific patterns precede generic ones.
"""

from __future__ import annotations

import re

from app.core import constants as C

# (regex, canonical_title, section_type, is_top_level)
_PATTERN_DEFS: list[tuple[str, str, str, bool]] = [
    (r"^item\s*1[a-z]?[.\s:–-]*business\b.*$", "Business Overview", "Business Overview", True),
    (r"^business overview$", "Business Overview", "Business Overview", True),
    (r"^item\s*1a[.\s:–-]*risk factors?\b.*$", "Risk Factors", "Risk Factors", True),
    (r"^risk factors?$", "Risk Factors", "Risk Factors", True),
    (r"^(risks? (and|&) uncertainties?)$", "Risks and Uncertainties", "Risk Factors", False),
    (
        r"^item\s*7[.\s:–-]*management'?s? (discussion and analysis|discussion).*md&a.*$",
        "Management Discussion and Analysis", "Management Discussion", True,
    ),
    (r"^(management'?s? )?(discussion and analysis|md&a).*(and|&)?\b(liquidity)?\b.*$", 
     "Management Discussion and Analysis", "Management Discussion", False),
    (r"^item\s*7a[.\s:–-]*(quantitative and qualitative disclosures? about )?market risk\b.*$",
     "Market Risk", "Management Discussion", True),
    (r"^market risk$", "Market Risk", "Management Discussion", False),
    (r"^item\s*8[.\s:–-]*financial statements?.*$", "Financial Statements", "Financial Statements", True),
    (r"^financial statements?( and supplementary data)?$", "Financial Statements", "Financial Statements", True),
    (r"^(consolidated |condensed )?statements? of operations$", "Consolidated Statements of Operations", "Income Statement", False),
    (r"^(consolidated |condensed )?income statements?$", "Income Statement", "Income Statement", False),
    (r"^income statement$", "Income Statement", "Income Statement", False),
    (r"^(consolidated |condensed )?balance sheets?$", "Balance Sheet", "Balance Sheet", False),
    (r"^balance sheet$", "Balance Sheet", "Balance Sheet", False),
    (r"^(consolidated |condensed )?statements? of cash flows?$", "Cash Flow Statement", "Cash Flow Statement", False),
    (r"^cash flow statement$", "Cash Flow Statement", "Cash Flow Statement", False),
    (r"^notes? to (the )?(consolidated )?financial statements?$", "Notes to Financial Statements", "Notes", False),
    (r"^notes?$", "Notes", "Notes", False),
    (r"^segment information$", "Segment Information", "Segment Information", False),
    (r"^(reportable )?segments?$", "Segments", "Segment Information", False),
    (r"^revenue$", "Revenue", "Other", False),
    (r"^operating expenses$", "Operating Expenses", "Other", False),
    (r"^(liquidity)( and capital resources)?$", "Liquidity and Capital Resources", "Management Discussion", False),
    (r"^capital resources$", "Capital Resources", "Management Discussion", False),
]

SECTION_PATTERNS: list[tuple[re.Pattern[str], str, str, bool]] = [
    (re.compile(pattern, re.IGNORECASE), title, section_type, top_level)
    for pattern, title, section_type, top_level in _PATTERN_DEFS
]

assert all(section_type in C.SECTION_TYPES for _, _, section_type, _ in _PATTERN_DEFS), (
    "SECTION_PATTERNS reference types missing from constants.SECTION_TYPES"
)
