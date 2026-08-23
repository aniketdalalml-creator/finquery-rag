"""DocumentService — documents, pages, sections, chunks, tables."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core import constants as C
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.document import Document, DocumentChunk, DocumentPage, DocumentSection
from app.models.table import FinancialTable, FinancialTableRow
from app.repositories.company import CompanyRepository
from app.repositories.document import (
    DocumentChunkRepository,
    DocumentPageRepository,
    DocumentRepository,
    DocumentSectionRepository,
)
from app.repositories.table import FinancialTableRepository
from app.schemas.document import (
    DocumentChunkCreate,
    DocumentCreate,
    DocumentPageCreate,
    DocumentSectionCreate,
)
from app.schemas.table import FinancialTableCreate


class DocumentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.pages = DocumentPageRepository(session)
        self.sections = DocumentSectionRepository(session)
        self.chunks = DocumentChunkRepository(session)
        self.tables = FinancialTableRepository(session)
        self.companies = CompanyRepository(session)

    # ── documents ────────────────────────────────────────────────

    def list_documents(self, limit: int = 50) -> list[Document]:
        return self.documents.list_all(limit=limit)

    def create_document(self, payload: DocumentCreate) -> Document:
        if payload.company_id is not None and (
            self.companies.get(payload.company_id) is None
        ):
            raise NotFoundError("Company", payload.company_id)

        if payload.file_hash:
            duplicate = self.documents.get_by_file_hash(
                payload.company_id, payload.file_hash
            )
            if duplicate is not None:
                raise ConflictError(
                    f"Document with file_hash {payload.file_hash!r} already "
                    f"exists (id={duplicate.id})"
                )

        document = Document(**payload.model_dump())
        return self.documents.add(document)

    def create_document_from_upload(
        self,
        *,
        company_id: int | None,
        document_type: str,
        title: str,
        source_url: str | None,
        source_name: str | None,
        file_path: str,
        file_hash: str,
    ) -> Document:
        """Create a record for an uploaded file (validation already done)."""
        if company_id is not None and self.companies.get(company_id) is None:
            raise NotFoundError("Company", company_id)
        document = Document(
            company_id=company_id,
            document_type=document_type if document_type in C.DOCUMENT_TYPES else "Other",
            title=title[:512],
            source_url=source_url,
            source_name=source_name[:255] if source_name else None,
            file_path=file_path,
            file_hash=file_hash,
            processing_status="uploaded",
        )
        return self.documents.add(document)

    def get_document(self, document_id: int) -> Document:
        document = self.documents.get(document_id)
        if document is None:
            raise NotFoundError("Document", document_id)
        return document

    def list_documents_for_company(
        self,
        company_id: int,
        document_type: str | None = None,
        fiscal_year: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        self._ensure_company(company_id)
        return self.documents.list_by_company(
            company_id,
            document_type=document_type,
            fiscal_year=fiscal_year,
            limit=max(1, min(limit, 200)),
            offset=max(0, offset),
        )

    # ── pages ────────────────────────────────────────────────────

    def add_page(self, document_id: int, payload: DocumentPageCreate) -> DocumentPage:
        self.get_document(document_id)
        if self.pages.get_by_number(document_id, payload.page_number) is not None:
            raise ConflictError(
                f"Page {payload.page_number} already exists for document {document_id}"
            )
        page = DocumentPage(document_id=document_id, **payload.model_dump())
        return self.pages.add(page)

    def list_pages(self, document_id: int) -> list[DocumentPage]:
        self.get_document(document_id)
        return self.pages.list_for_document(document_id)

    # ── sections ─────────────────────────────────────────────────

    def add_section(
        self, document_id: int, payload: DocumentSectionCreate
    ) -> DocumentSection:
        self.get_document(document_id)
        data = payload.model_dump()
        parent_id = data.pop("parent_section_id")
        if parent_id is not None:
            parent = self.sections.get(parent_id)
            if parent is None or parent.document_id != document_id:
                raise ValidationError(
                    f"parent_section_id {parent_id} does not belong to "
                    f"document {document_id}"
                )
        section = DocumentSection(
            document_id=document_id, parent_section_id=parent_id, **data
        )
        return self.sections.add(section)

    def list_sections(self, document_id: int) -> list[DocumentSection]:
        self.get_document(document_id)
        return self.sections.list_for_document(document_id)

    # ── chunks ───────────────────────────────────────────────────

    def add_chunk(
        self, document_id: int, payload: DocumentChunkCreate
    ) -> DocumentChunk:
        self.get_document(document_id)
        if payload.section_id is not None:
            section = self.sections.get(payload.section_id)
            if section is None or section.document_id != document_id:
                raise ValidationError(
                    f"section_id {payload.section_id} does not belong to "
                    f"document {document_id}"
                )
        if self.chunks.get_by_index(document_id, payload.chunk_index) is not None:
            raise ConflictError(
                f"chunk_index {payload.chunk_index} already exists for "
                f"document {document_id}"
            )
        chunk = DocumentChunk(document_id=document_id, **payload.model_dump())
        return self.chunks.add(chunk)

    def list_chunks(self, document_id: int) -> list[DocumentChunk]:
        self.get_document(document_id)
        return self.chunks.list_for_document(document_id)

    # ── tables ───────────────────────────────────────────────────

    def add_table(self, document_id: int, payload: FinancialTableCreate) -> FinancialTable:
        self.get_document(document_id)
        if payload.source_chunk_id is not None:
            chunk = self.chunks.get(payload.source_chunk_id)
            if chunk is None or chunk.document_id != document_id:
                raise ValidationError(
                    f"source_chunk_id {payload.source_chunk_id} does not belong "
                    f"to document {document_id}"
                )
        table = FinancialTable(
            document_id=document_id,
            source_chunk_id=payload.source_chunk_id,
            page_number=payload.page_number,
            title=payload.title,
            headers=list(payload.headers),
            units=payload.units,
            currency=payload.currency,
            extraction_confidence=payload.extraction_confidence,
        )
        self.tables.add(table)
        for row in sorted(payload.rows, key=lambda r: r.row_index):
            self.tables.add_row(
                FinancialTableRow(
                    table_id=table.id,
                    row_index=row.row_index,
                    row_label=row.row_label,
                    cells=list(row.cells),
                )
            )
        return table

    def get_table(self, document_id: int, table_id: int) -> FinancialTable:
        self.get_document(document_id)
        table = self.tables.get_with_rows(table_id)
        if table is None or table.document_id != document_id:
            raise NotFoundError("FinancialTable", table_id)
        return table

    def list_tables(self, document_id: int) -> list[FinancialTable]:
        self.get_document(document_id)
        tables = self.tables.list_for_document(document_id)
        for table in tables:
            table.rows  # load ordered rows (lazy)
        return tables

    # ── helpers ──────────────────────────────────────────────────

    def _ensure_company(self, company_id: int) -> None:
        if self.companies.get(company_id) is None:
            raise NotFoundError("Company", company_id)
