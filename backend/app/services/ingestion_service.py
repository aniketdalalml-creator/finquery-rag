"""IngestionService — upload validation, dedup, processing dispatch."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.ingestion.loaders.registry import get_loader
from app.ingestion.pipeline import (
    DocumentIngestionPipeline,
    IngestionResult,
)
from app.ingestion.pipeline.observability import get_ingestion_stats
from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.services.document_service import DocumentService
from app.services.storage_service import DocumentStorageService

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MiB


class IngestionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.document_service = DocumentService(session)

    def upload_document(
        self,
        *,
        filename: str,
        data: bytes,
        storage: DocumentStorageService,
        company_id: int | None = None,
        document_type: str = "Other",
        title: str | None = None,
        source_url: str | None = None,
        source_name: str | None = None,
    ) -> tuple[Document, bool]:
        """Validate + store a file and create its document record.

        Returns (document, duplicate). A duplicate returns the existing
        record without re-storing anything.
        """
        if not data:
            raise ValidationError("Uploaded file is empty")
        if len(data) > MAX_UPLOAD_BYTES:
            raise ValidationError(
                f"File exceeds upload limit ({MAX_UPLOAD_BYTES // (1024 * 1024)} MiB)"
            )
        try:
            get_loader(filename)
        except Exception as exc:
            raise ValidationError(str(exc)) from exc

        # Hash before storing so duplicates never touch object storage.
        import hashlib

        file_hash = hashlib.sha256(data).hexdigest()
        existing = self.documents.get_by_file_hash(company_id, file_hash)
        if existing is not None:
            return existing, True

        key, _digest = storage.store_document(
            company_id, filename, data
        )
        document = self.document_service.create_document_from_upload(
            company_id=company_id,
            document_type=document_type,
            title=title or filename.rsplit("/", 1)[-1],
            source_url=source_url,
            source_name=source_name,
            file_path=key,
            file_hash=file_hash,
        )
        logger.info(
            "document uploaded id=%s filename=%s bytes=%d",
            document.id,
            filename,
            len(data),
        )
        return document, False

    def mark_queued(self, document_id: int) -> Document:
        document = self.documents.get(document_id)
        if document is None:
            raise NotFoundError("Document", document_id)
        if document.processing_status == "processing":
            raise ConflictError(f"Document {document_id} is already being processed")
        document.processing_status = "queued"
        self.session.commit()
        return document


def run_ingestion(document_id: int, force: bool = False) -> dict:
    """Background-task entrypoint: owns its own DB session."""
    from app.db.session import SessionLocal
    from app.storage import get_storage

    session = SessionLocal()
    try:
        pipeline = DocumentIngestionPipeline(
            session, DocumentStorageService(get_storage())
        )
        result: IngestionResult = pipeline.process(document_id, force=force)
        stats = get_ingestion_stats().snapshot()
        return {
            "document_id": document_id,
            "status": result.status,
            "stages": [s.to_dict() for s in result.stages],
            "stats": stats,
        }
    finally:
        session.close()
