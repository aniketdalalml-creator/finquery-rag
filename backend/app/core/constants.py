"""Domain type registries.

These are application-level vocabularies, NOT database enums: the columns are
plain strings so new types can be added here without a schema migration.
"""

from __future__ import annotations

DOCUMENT_TYPES: frozenset[str] = frozenset(
    {
        "10-K",
        "10-Q",
        "8-K",
        "Annual Report",
        "Quarterly Report",
        "Investor Presentation",
        "Earnings Release",
        "Financial Statement",
        "Research Report",
        "Other",
    }
)

# Ingestion lifecycle (Prompt 3). `pending`/`completed` are legacy aliases
# kept for backward compatibility with pre-existing rows.
PROCESSING_STATUSES: frozenset[str] = frozenset(
    {
        "uploaded",
        "queued",
        "processing",
        "processed",
        "partially_processed",
        "failed",
        "pending",
        "completed",
    }
)

# Document-level ingestion stages (for logging / stage results).
INGESTION_STAGES: tuple[str, ...] = (
    "validate",
    "load",
    "ocr",
    "clean",
    "section_detection",
    "chunking",
    "table_extraction",
    "metadata_extraction",
    "metric_extraction",
    "persist",
)

EXTRACTION_METHODS: frozenset[str] = frozenset({"text", "ocr", "table", "mixed"})

SECTION_TYPES: frozenset[str] = frozenset(
    {
        "Risk Factors",
        "Management Discussion",
        "Financial Statements",
        "Balance Sheet",
        "Income Statement",
        "Cash Flow Statement",
        "Notes",
        "Business Overview",
        "Segment Information",
        "Other",
    }
)

CHUNK_TYPES: frozenset[str] = frozenset(
    {
        "text",
        "financial_metric",
        "table",
        "table_row",
        "table_cell",
        "section_summary",
    }
)

METRIC_TYPES: frozenset[str] = frozenset(
    {
        "income_statement",
        "balance_sheet",
        "cash_flow",
        "per_share",
        "margin",
        "ratio",
        "valuation",
        "other",
    }
)

FISCAL_QUARTERS: frozenset[str] = frozenset({"Q1", "Q2", "Q3", "Q4"})
