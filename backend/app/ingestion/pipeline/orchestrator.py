"""DocumentIngestionPipeline — orchestrates every ingestion stage.

Stages are individually testable and isolated via StageResult recorders.
A failing stage does not necessarily fail the document: text/section/
metric failures mark the document `failed`, while table/metric extraction
problems degrade it to `partially_processed`.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import config
from app.core.constants import FISCAL_QUARTERS
from app.ingestion.chunking.chunker import FinanceAwareChunker, PlannedChunk
from app.ingestion.cleaners import CleaningReport, DocumentCleaner
from app.ingestion.loaders.base import RawDocument, UnsupportedFormatError
from app.ingestion.loaders.registry import get_loader
from app.ingestion.metadata.extractor import MetadataExtractor
from app.ingestion.metrics.detector import MetricDetector, parse_currency
from app.ingestion.ocr.base import OCRProvider, OCRError
from app.ingestion.pipeline.results import (
    FAILED,
    PARTIAL,
    SUCCESS,
    IngestionResult,
    stage_partial,
    stage_skip as results_skip,
)
from app.ingestion.pipeline.observability import get_ingestion_stats
from app.ingestion.sectioning.detector import DetectedSection, SectionDetector
from app.ingestion.tables.extractor import DetectedTable, TableExtractor
from app.models.document import Document, DocumentChunk, DocumentPage, DocumentSection
from app.models.metric import FinancialMetric
from app.models.table import FinancialTable, FinancialTableRow
from app.repositories.company import CompanyRepository
from app.services.storage_service import DocumentStorageService

logger = logging.getLogger(__name__)

# Statuses that allow (re)processing.
_PROCESSABLE = {"uploaded", "queued", "pending", "failed", "partially_processed", "completed"}


class PipelineError(Exception):
    pass


class DocumentIngestionPipeline:
    def __init__(
        self,
        session: Session,
        storage: DocumentStorageService,
        ocr_provider: OCRProvider | None = None,
        chunker: FinanceAwareChunker | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.ocr = ocr_provider
        self.chunker = chunker or FinanceAwareChunker()
        self.cleaner = DocumentCleaner()
        self.section_detector = SectionDetector()
        self.table_extractor = TableExtractor()
        self.metadata_extractor = MetadataExtractor()
        self.metric_detector = MetricDetector()
        self.companies = CompanyRepository(session)
        self.stats = get_ingestion_stats()

    # ── public entrypoint ────────────────────────────────────────

    def process(self, document_id: int, force: bool = False) -> IngestionResult:
        started = time.perf_counter()
        document = self.session.get(Document, document_id)
        if document is None:
            raise PipelineError(f"Document {document_id} not found")

        result = IngestionResult(document_id=document_id, status="failed")
        # Pre-bind so a raising load stage still hits the guard below
        # instead of crashing on an unassigned variable.
        raw_doc: RawDocument | None = None
        try:
            with result.add("validate"):
                self._validate(document, force)

            self._mark_processing(document)

            with result.add("load") as rec:
                raw_doc = self._load(document)
                rec.details = {
                    "format": raw_doc.format,
                    "pages": len(raw_doc.pages),
                }

            if raw_doc is None or not raw_doc.pages:
                # Every downstream stage needs the loaded document; stop here
                # so a load failure surfaces as `failed`, never as a crash.
                # The finally block below records stats and returns result.
                result.status = "failed"
                result.error = "load produced no pages"
                self._mark_finished(document, "failed", error=result.error)
                self.session.commit()
                return result

            pages_payload, _ocr_notes = self._run_ocr_stage(result, document, raw_doc)

            cleaned_map: dict[int, str] = {}
            cleaning_reports: dict[int, CleaningReport] = {}
            with result.add("clean") as rec:
                raw_map = {p.page_number: p.text for p in raw_doc.pages}
                reports = self.cleaner.clean_document(raw_map)
                cleaning_reports = {
                    n: report for n, (_text, report) in reports.items()
                }
                cleaned_map = {n: text for n, (text, _report) in reports.items()}
                rec.details = {"pages_cleaned": len(cleaned_map)}

            sections_tree: list[DetectedSection] = []
            with result.add("section_detection") as rec:
                sections_tree = self.section_detector.detect(cleaned_map)
                rec.details = {
                    "roots": len(sections_tree),
                    "total": sum(len(root.flat) for root in sections_tree),
                }

            detected_tables: list[DetectedTable] = []
            with result.add("table_extraction") as rec:
                detected_tables = self._extract_tables(cleaned_map)
                failed_tables = [t for t in detected_tables if not t.extraction_ok]
                rec.details = {
                    "tables": len(detected_tables),
                    "low_confidence": len(failed_tables),
                }
                if detected_tables and failed_tables == detected_tables:
                    raise stage_partial(
                        f"All {len(failed_tables)} table candidates unreliable; "
                        f"raw text preserved",
                        {"pages": sorted({t.page_number for t in failed_tables})},
                    )

            detected_meta = None
            with result.add("metadata_extraction") as rec:
                detected_meta = self.metadata_extractor.extract(
                    cleaned_map, document.file_path or ""
                )
                rec.details = detected_meta.as_dict()

            planned_chunks: list[PlannedChunk] = []
            with result.add("chunking") as rec:
                tables_payload = [self._table_payload(t) for t in detected_tables]
                sections_payload = self._sections_payload(sections_tree, cleaned_map)
                planned_chunks = self.chunker.build_chunks(
                    cleaned_map, sections_payload, tables_payload
                )
                rec.details = {"chunks": len(planned_chunks)}

            metrics_detected = []
            with result.add("metric_extraction") as rec:
                metrics_detected = self._detect_metrics(planned_chunks)
                rec.details = {"metrics": len(metrics_detected)}

            with result.add("persist") as rec:
                counts = self._persist(
                    document,
                    raw_doc,
                    cleaned_map,
                    cleaning_reports,
                    pages_payload,
                    sections_tree,
                    planned_chunks,
                    detected_tables,
                    detected_meta,
                    metrics_detected,
                )
                rec.details = counts
                result.counts.update(counts)

            hard_failures = [
                s for s in result.stages
                if s.status == FAILED and s.stage not in ("table_extraction", "metric_extraction", "ocr")
            ]
            soft_failures = [
                s for s in result.stages if s.status in (PARTIAL, FAILED)
            ]
            if hard_failures:
                result.status = "failed"
                self._mark_finished(document, "failed", error=hard_failures[0].error)
            elif soft_failures:
                result.status = "partially_processed"
                self._mark_finished(document, "partially_processed")
            else:
                result.status = "processed"
                self._mark_finished(document, "processed")
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            logger.exception("ingestion pipeline crashed document_id=%s", document_id)
            result.status = "failed"
            fresh = self.session.get(Document, document_id)
            if fresh is not None:
                self._mark_finished(fresh, "failed", error=f"{type(exc).__name__}: {exc}")
                self.session.commit()
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            self.stats.record_document(result.status, duration_ms)
            self.stats.bump(
                pages_processed=result.counts.get("pages", 0),
                tables_extracted=result.counts.get("tables", 0),
                metrics_extracted=result.counts.get("metrics", 0),
                chunks_created=result.counts.get("chunks", 0),
            )
            result.counts.setdefault("duration_ms", int(duration_ms))
            logger.info(
                "ingestion finished document_id=%s status=%s stages=%s",
                document_id,
                result.status,
                [(s.stage, s.status) for s in result.stages],
            )
        return result

    # ── stages ───────────────────────────────────────────────────

    @staticmethod
    def _validate(document: Document, force: bool) -> None:
        if not document.file_path:
            raise PipelineError(
                f"Document {document.id} has no stored file (upload first)"
            )
        if force is False and document.processing_status == "processing":
            raise PipelineError(
                f"Document {document.id} is already being processed"
            )

    def _load(self, document: Document) -> RawDocument:
        data = self.storage.download(document.file_path)
        filename = (document.file_path or "").rsplit("/", 1)[-1]
        loader = get_loader(filename)
        return loader.load(data, filename)

    def _run_ocr_stage(
        self, result: IngestionResult, document: Document, raw_doc: RawDocument
    ) -> tuple[dict[str, Any], list[str]]:
        """Fill page payloads; run OCR only where the loader flagged pages."""
        notes: list[str] = []
        page_metadata: dict[int, dict] = {
            p.page_number: dict(p.metadata) for p in raw_doc.pages
        }
        ocr_texts: dict[int, str] = {}

        with result.add("ocr") as rec:
            flagged = [p.page_number for p in raw_doc.pages if p.needs_ocr]
            if not flagged:
                raise results_skip("no image-only pages")
            if self.ocr is None or not self.ocr.is_available():
                raise results_skip(
                    f"{len(flagged)} candidate page(s) need OCR but no "
                    f"provider is available"
                )
            pdf_bytes = self.storage.download(document.file_path)
            for page_number in flagged:
                try:
                    ocr_result = self.ocr.recognize_page(pdf_bytes, page_number)
                    ocr_texts[page_number] = ocr_result.text
                    page_metadata.setdefault(page_number, {})[
                        "ocr_engine"
                    ] = ocr_result.engine
                except OCRError as exc:
                    notes.append(f"page {page_number}: {exc}")
            rec.details = {"ocr_pages": len(ocr_texts), "notes": len(notes)}
            if notes and not ocr_texts:
                raise stage_partial("; ".join(notes), {"pages": flagged})

        return {"ocr_texts": ocr_texts, "page_metadata": page_metadata}, notes

    def _clean(
        self, raw_doc: RawDocument, _unused: dict
    ) -> dict[int, str]:
        raw_map = {p.page_number: p.text for p in raw_doc.pages}
        cleaned = self.cleaner.clean_document(raw_map)
        return {n: text for n, (text, _report) in cleaned.items()}

    def _extract_tables(self, cleaned_map: dict[int, str]) -> list[DetectedTable]:
        tables: list[DetectedTable] = []
        for page_number in sorted(cleaned_map):
            tables.extend(self.table_extractor.extract_from_page(page_number, cleaned_map[page_number]))
        return tables

    def _detect_metrics(self, planned_chunks: list[PlannedChunk]) -> list:
        return self.metric_detector.detect_in_chunks(
            [
                {
                    "index": chunk.chunk_index,
                    "text": chunk.text,
                    "pages": [chunk.page_start],
                }
                for chunk in planned_chunks
                if chunk.chunk_type == "text"
            ]
        )

    # ── persistence ──────────────────────────────────────────────

    def _persist(
        self,
        document: Document,
        raw_doc: RawDocument,
        cleaned_map: dict[int, str],
        cleaning_reports: dict[int, CleaningReport],
        pages_payload: dict[str, Any],
        sections_tree: list[DetectedSection],
        planned_chunks: list[PlannedChunk],
        detected_tables: list[DetectedTable],
        detected_meta,
        metrics_detected: list,
    ) -> dict[str, int]:
        # Reprocessing: clear previously derived rows (ORM cascade).
        self._clear_derived(document)

        ocr_texts: dict[int, str] = pages_payload["ocr_texts"]

        for page in raw_doc.pages:
            method = "text"
            if page.page_number in ocr_texts and page.text.strip():
                method = "mixed"
            elif page.page_number in ocr_texts:
                method = "ocr"
            meta = dict(page.metadata)
            meta.update(pages_payload["page_metadata"].get(page.page_number, {}))
            if page.page_number in cleaning_reports:
                report = cleaning_reports[page.page_number]
                meta["cleaning"] = {
                    "removed_header_lines": report.removed_header_lines,
                    "removed_footer_lines": report.removed_footer_lines,
                    "removed_page_numbers": report.removed_page_numbers,
                    "dehyphenated_joins": report.dehyphenated_joins,
                }
            effective_text = ocr_texts.get(page.page_number) or page.text
            document.pages.append(
                DocumentPage(
                    page_number=page.page_number,
                    raw_text=effective_text,
                    cleaned_text=cleaned_map.get(page.page_number, ""),
                    extraction_method=method,
                    extraction_metadata=meta,
                )
            )

        # Sections: parents flush before children so the self-FK is satisfied.
        section_id_map: dict[int, int] = {}
        for root in sections_tree:
            for node in root.flat:
                parent_obj = getattr(node, "parent", None)
                parent_id = (
                    section_id_map.get(id(parent_obj)) if parent_obj else None
                )
                section_row = DocumentSection(
                    section_title=node.title[:512],
                    section_type=node.section_type,
                    page_start=node.page_start,
                    page_end=node.page_end,
                    parent_section_id=parent_id,
                )
                document.sections.append(section_row)
                self.session.flush()
                section_id_map[id(node)] = section_row.id

        inserted_by_key = {
            (s.section_title, s.page_start): s for s in document.sections
        }

        # Chunks.
        section_rows_by_title_page = inserted_by_key
        chunk_rows: list[DocumentChunk] = []
        for chunk in planned_chunks:
            section_row = self._find_section_row(
                section_rows_by_title_page, chunk.metadata.get("section_title"),
                chunk.page_start,
            )
            chunk_row = DocumentChunk(
                chunk_index=chunk.chunk_index,
                chunk_type=chunk.chunk_type,
                text=chunk.text,
                token_count=chunk.token_count,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                section_id=(
                    section_row.id if section_row is not None else None
                ),
                chunk_metadata={
                    **chunk.metadata,
                    "section_path": chunk.section_path,
                },
            )
            document.chunks.append(chunk_row)
            chunk_rows.append(chunk_row)
        self.session.flush()

        # Tables (+ rows), linked to their rendered table-chunk when present.
        chunk_by_table_ref = {
            (c.chunk_metadata.get("table_page"), c.chunk_metadata.get("table_pos")): c
            for c in chunk_rows
            if c.chunk_type == "table"
        }
        for position, table in enumerate(detected_tables):
            source_chunk = chunk_by_table_ref.get((table.page_number, position))
            table_row_model = FinancialTable(
                page_number=table.page_number,
                title=(table.title or "Table")[:512],
                headers=[str(h) for h in table.headers] if table.extraction_ok else [],
                units=table.units,
                currency=table.currency,
                extraction_confidence=table.confidence,
                source_chunk_id=source_chunk.id if source_chunk is not None else None,
            )
            document.tables.append(table_row_model)
            if table.extraction_ok:
                for row_index, cells in enumerate(table.rows):
                    table_row_model.rows.append(
                        FinancialTableRow(
                            row_index=row_index,
                            row_label=(cells[0][:512] if cells else None),
                            cells=[str(c) for c in cells],
                        )
                    )
            else:
                # Preserve raw text without inventing structure.
                table_row_model.rows.append(
                    FinancialTableRow(
                        row_index=0,
                        row_label=None,
                        cells=[table.raw_text],
                    )
                )
        self.session.flush()

        # Document-level metadata from confident extractions.
        if detected_meta is not None:
            self._apply_metadata(document, detected_meta)

        # Metrics require a company; resolve via ticker when possible.
        company_id = document.company_id
        if company_id is None and detected_meta is not None and detected_meta.ticker:
            company = self.companies.get_by_ticker(detected_meta.ticker.value)
            if company is not None:
                company_id = company.id
                document.company_id = company.id

        metric_count = 0
        if company_id is None:
            logger.info(
                "metrics skipped document_id=%s reason=no company resolution",
                document.id,
            )
        else:
            chunk_by_index = {c.chunk_index: c for c in chunk_rows}
            doc_currency = document.currency
            doc_fiscal_year = document.fiscal_year
            seen_metric_keys: set[tuple[str, str, int]] = set()
            for metric in metrics_detected:
                resolved = metric.resolved_value()
                if resolved is None:
                    continue
                # Overlapping section spans can produce identical chunks;
                # never persist the same fact twice per document.
                dedupe_key = (
                    metric.normalized_metric_name,
                    str(resolved),
                    metric.page_number,
                )
                if dedupe_key in seen_metric_keys:
                    continue
                seen_metric_keys.add(dedupe_key)

                period_hint = metric.period_hint or ""
                fiscal_year = doc_fiscal_year
                fiscal_quarter = None
                if period_hint.startswith("FY"):
                    fiscal_year = int(period_hint[2:]) or fiscal_year
                elif period_hint.startswith("Q"):
                    parts = period_hint.split()
                    fiscal_quarter = parts[0]
                    if len(parts) > 1 and parts[1].isdigit():
                        fiscal_year = int(parts[1])

                unit = "%" if metric.percent else (metric.scale_word or "units")
                document_metric = FinancialMetric(
                    company_id=company_id,
                    document_id=document.id,
                    metric_name=metric.raw_label[:255],
                    normalized_metric_name=metric.normalized_metric_name[:255],
                    value=resolved,
                    unit=unit[:32],
                    currency=None if metric.percent else parse_currency(
                        metric.currency_symbol, doc_currency
                    ),
                    fiscal_year=fiscal_year,
                    fiscal_quarter=fiscal_quarter if fiscal_quarter in FISCAL_QUARTERS else None,
                    metric_type=metric.metric_type,
                    source_page=metric.page_number,
                    source_chunk_id=(
                        chunk_by_index[metric.chunk_index].id
                        if metric.chunk_index in chunk_by_index
                        else None
                    ),
                    confidence=metric.confidence,
                )
                self.session.add(document_metric)
                metric_count += 1

        document.page_count = len(raw_doc.pages)
        self.session.flush()
        return {
            "pages": len(raw_doc.pages),
            "sections": len(inserted_by_key),
            "chunks": len(chunk_rows),
            "tables": len(detected_tables),
            "metrics": metric_count,
        }

    def _clear_derived(self, document: Document) -> None:
        # Force-load then clear each collection, and flush immediately:
        # the unit of work runs INSERTs before DELETEs otherwise, which
        # would trip the unique page/chunk constraints on reprocessing.
        collections = (
            document.pages,
            document.sections,
            document.chunks,
            document.tables,
        )
        for collection in collections:
            _ = list(collection)
            collection.clear()
        # Metrics hang off Company, so clear this document's rows explicitly.
        self.session.query(FinancialMetric).filter(
            FinancialMetric.document_id == document.id
        ).delete(synchronize_session=False)
        self.session.flush()

    @staticmethod
    def _find_section_row(by_key, title, page_start):
        if title is None:
            return None
        for (row_title, row_page), row in by_key.items():
            if row_title == title and row_page <= (page_start or row_page):
                return row
        return None

    def _apply_metadata(self, document: Document, meta) -> None:
        if meta.document_type is not None and meta.document_type.confidence >= 0.6:
            document.document_type = meta.document_type.value
        if meta.fiscal_year is not None and meta.fiscal_year.confidence >= 0.6:
            document.fiscal_year = int(meta.fiscal_year.value)
        if meta.fiscal_quarter is not None and meta.fiscal_quarter.confidence >= 0.7:
            if meta.fiscal_quarter.value in FISCAL_QUARTERS:
                document.fiscal_quarter = meta.fiscal_quarter.value
        if meta.period_start is not None and meta.period_start.confidence >= 0.6:
            document.reporting_period_start = meta.period_start.value
        if meta.period_end is not None and meta.period_end.confidence >= 0.6:
            end_value = meta.period_end.value
            start_value = (
                meta.period_start.value if meta.period_start is not None else None
            )
            if start_value is None or end_value >= start_value:
                document.reporting_period_end = end_value
        if meta.currency is not None and meta.currency.confidence >= 0.7:
            code = meta.currency.value
            if isinstance(code, str) and len(code) == 3 and code.isalpha():
                document.currency = code.upper()

    # ── helpers ──────────────────────────────────────────────────

    def _mark_processing(self, document: Document) -> None:
        document.processing_status = "processing"
        document.processing_started_at = datetime.now(timezone.utc)
        document.processing_completed_at = None
        document.processing_error = None
        self.session.commit()

    def _mark_finished(
        self, document: Document, status: str, error: str | None = None
    ) -> None:
        document.processing_status = status
        document.processing_completed_at = datetime.now(timezone.utc)
        document.processing_error = error

    @staticmethod
    def _table_payload(table: DetectedTable) -> dict:
        return {
            "page_number": table.page_number,
            "title": table.title,
            "headers": table.headers,
            "rows": [{"cells": cells} for cells in table.rows],
            "raw_text": table.raw_text,
        }

    @staticmethod
    def _sections_payload(
        roots: list[DetectedSection], cleaned_map: dict[int, str]
    ) -> list[dict]:
        """Flatten the tree into ordered payloads with per-section lines."""
        payloads: list[dict] = []
        ordered_nodes: list[DetectedSection] = []
        for root in roots:
            ordered_nodes.extend(root.flat)

        for position, node in enumerate(ordered_nodes):
            end = node.page_end or node.page_start
            lines: list[tuple[int, str]] = []
            for page_number in range(node.page_start, end + 1):
                if page_number not in cleaned_map:
                    continue
                for line in cleaned_map[page_number].splitlines():
                    if line.strip() and line.strip() != node.title:
                        lines.append((page_number, line))
            path = [ancestor.title for ancestor in node.path_to_root()]
            payloads.append(
                {
                    "title": node.title,
                    "section_type": node.section_type,
                    "page_start": node.page_start,
                    "page_end": end,
                    "path": path,
                    "lines": lines,
                }
            )
        return payloads
