"""Repositories for documents, pages, sections and chunks."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.document import Document, DocumentChunk, DocumentPage, DocumentSection
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    def get_by_file_hash(self, company_id: int | None, file_hash: str) -> Document | None:
        stmt = select(Document).where(
            Document.company_id == company_id,
            func.lower(Document.file_hash) == file_hash.lower(),
        )
        return self._scalar(stmt)

    def list_by_company(
        self,
        company_id: int,
        document_type: str | None = None,
        fiscal_year: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.company_id == company_id)
            .order_by(
                Document.filing_date.is_(None),
                Document.filing_date.desc(),
                Document.id.desc(),
            )
        )
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if fiscal_year is not None:
            stmt = stmt.where(Document.fiscal_year == fiscal_year)
        stmt = stmt.limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())


class DocumentPageRepository(BaseRepository[DocumentPage]):
    model = DocumentPage

    def get_by_number(self, document_id: int, page_number: int) -> DocumentPage | None:
        stmt = select(DocumentPage).where(
            DocumentPage.document_id == document_id,
            DocumentPage.page_number == page_number,
        )
        return self._scalar(stmt)

    def list_for_document(self, document_id: int) -> list[DocumentPage]:
        stmt = (
            select(DocumentPage)
            .where(DocumentPage.document_id == document_id)
            .order_by(DocumentPage.page_number)
        )
        return list(self.session.scalars(stmt).all())

    def count_for_document(self, document_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(DocumentPage)
            .where(DocumentPage.document_id == document_id)
        )
        return int(self.session.scalar(stmt))


class DocumentSectionRepository(BaseRepository[DocumentSection]):
    model = DocumentSection

    def list_for_document(
        self, document_id: int, section_type: str | None = None
    ) -> list[DocumentSection]:
        stmt = (
            select(DocumentSection)
            .where(DocumentSection.document_id == document_id)
            .order_by(
                DocumentSection.page_start.is_(None),
                DocumentSection.page_start,
                DocumentSection.id,
            )
        )
        if section_type:
            stmt = stmt.where(DocumentSection.section_type == section_type)
        return list(self.session.scalars(stmt).all())


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    model = DocumentChunk

    def get_by_index(self, document_id: int, chunk_index: int) -> DocumentChunk | None:
        stmt = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.chunk_index == chunk_index,
        )
        return self._scalar(stmt)

    def list_for_document(
        self,
        document_id: int,
        chunk_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        if chunk_type:
            stmt = stmt.where(DocumentChunk.chunk_type == chunk_type)
        stmt = stmt.limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())

    def count_for_document(self, document_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
        )
        return int(self.session.scalar(stmt))
