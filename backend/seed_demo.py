"""Seed the database with PUBLIC demo data.

Uses well-known, publicly reported figures from Apple Inc.'s FY2024 Form 10-K
(SEC EDGAR) purely as demo/sample content to verify the storage layer.
Run from backend/:
    python seed_demo.py [--force]
"""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, register_sqlite_pragmas
from app.models.company import Company
from app.models.document import Document, DocumentChunk, DocumentPage, DocumentSection
from app.models.metric import FinancialMetric
from app.models.table import FinancialTable, FinancialTableRow
from app.services.metric_service import normalize_metric_name

register_sqlite_pragmas(engine)

APPLE_10K_URL = (
    "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm"
)


def seed(force: bool = False) -> None:
    Base.metadata.create_all(engine)  # convenience only; migrations are canonical

    with Session(engine) as session:
        existing = session.execute(
            select(Company).where(Company.ticker == "AAPL")
        ).scalar_one_or_none()
        if existing is not None and not force:
            print("Demo data already present (AAPL). Use --force to re-seed.")
            return
        if existing is not None:
            session.delete(existing)
            # Flush now: unit-of-work runs INSERTs before DELETEs otherwise,
            # which would trip the unique company indexes.
            session.flush()

        apple = Company(
            legal_name="Apple Inc.",
            display_name="Apple",
            ticker="AAPL",
            exchange="NASDAQ",
            country="US",
            sector="Technology",
            industry="Consumer Electronics",
        )
        session.add(apple)
        session.flush()

        document = Document(
            company_id=apple.id,
            document_type="10-K",
            title="Apple Inc. Form 10-K FY2024",
            source_url=APPLE_10K_URL,
            source_name="SEC EDGAR",
            filing_date=date(2024, 11, 1),
            reporting_period_start=date(2023, 10, 1),
            reporting_period_end=date(2024, 9, 28),
            fiscal_year=2024,
            currency="USD",
            language="en",
            file_hash="demo-aapl-10k-fy2024",
            page_count=80,
            processing_status="completed",
        )
        session.add(document)
        session.flush()

        income_section = DocumentSection(
            document_id=document.id,
            section_title="Income Statement",
            section_type="Income Statement",
            page_start=30,
            page_end=33,
            text="Consolidated statements of operations.",
        )
        risk_section = DocumentSection(
            document_id=document.id,
            section_title="Risk Factors",
            section_type="Risk Factors",
            page_start=5,
            page_end=18,
        )
        session.add_all([income_section, risk_section])
        session.flush()

        child_risk = DocumentSection(
            document_id=document.id,
            parent_section_id=risk_section.id,
            section_title="Supply Chain Risk",
            section_type="Risk Factors",
            page_start=9,
            page_end=11,
        )
        session.add(child_risk)
        session.flush()

        page = DocumentPage(
            document_id=document.id,
            page_number=31,
            raw_text="Total net sales ... $391,035 ... Net income $93,736",
            cleaned_text="Total net sales $391,035 million; Net income $93,736 million.",
            extraction_method="text",
        )
        session.add(page)

        chunk = DocumentChunk(
            document_id=document.id,
            section_id=income_section.id,
            chunk_index=0,
            chunk_type="financial_metric",
            text=(
                "Total net sales were $391,035 million for fiscal 2024. "
                "Net income was $93,736 million."
            ),
            token_count=20,
            chunk_metadata={"page": 31},
        )
        session.add(chunk)
        session.flush()

        metrics = [
            ("Revenue", "391035000000", "income_statement"),
            ("Net Income", "93736000000", "income_statement"),
            ("Gross Margin", "46.2", "margin"),
        ]
        for name, value, metric_type in metrics:
            session.add(
                FinancialMetric(
                    company_id=apple.id,
                    document_id=document.id,
                    metric_name=name,
                    normalized_metric_name=normalize_metric_name(name),
                    value=Decimal(value),
                    unit="%" if metric_type == "margin" else "USD",
                    currency=None if metric_type == "margin" else "USD",
                    period_start=date(2023, 10, 1),
                    period_end=date(2024, 9, 28),
                    fiscal_year=2024,
                    metric_type=metric_type,
                    source_page=31,
                    source_chunk_id=chunk.id,
                    confidence=Decimal("0.99"),
                )
            )

        table = FinancialTable(
            document_id=document.id,
            source_chunk_id=chunk.id,
            page_number=31,
            title="Net sales by category (FY2024, $M)",
            headers=["Category", "FY2024"],
            extraction_confidence=Decimal("0.97"),
        )
        session.add(table)
        session.flush()
        rows = [
            ("iPhone", "201,183"),
            ("Services", "96,169"),
            ("Mac", "29,984"),
        ]
        for index, (label, value) in enumerate(rows):
            session.add(
                FinancialTableRow(
                    table_id=table.id,
                    row_index=index,
                    row_label=label,
                    cells=[label, value],
                )
            )

        session.commit()

    print("Seeded public demo data: Apple Inc. FY2024 10-K (metrics, sections, table).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-seed if present")
    seed(parser.parse_args().force)
