"""Document, page, section, chunk and table endpoints."""

from __future__ import annotations

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import (
    DocumentChunkCreate,
    DocumentChunkRead,
    DocumentCreate,
    DocumentListRead,
    DocumentPageCreate,
    DocumentPageRead,
    DocumentRead,
    DocumentSectionCreate,
    DocumentSectionRead,
)
from app.schemas.table import FinancialTableCreate, FinancialTableRead
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService, run_ingestion
from app.services.storage_service import DocumentStorageService
from app.storage import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])


def _service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


# ── ingestion workflow (upload → process → status) ───────────────


@router.get("", response_model=list[DocumentListRead])
def list_documents(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """All documents, newest first (documents list view)."""
    service = DocumentService(db)
    rows = []
    for document in service.list_documents(limit=limit):
        company_name = None
        if document.company is not None:
            company_name = (
                document.company.display_name or document.company.legal_name
            )
        rows.append(
            DocumentListRead(
                id=document.id,
                company_id=document.company_id,
                company_name=company_name,
                title=document.title,
                document_type=document.document_type,
                filing_date=document.filing_date,
                processing_status=document.processing_status,
                created_at=document.created_at,
            )
        )
    return rows


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    company_id: int | None = Form(default=None),
    document_type: str = Form(default="Other"),
    source_url: str | None = Form(default=None),
    source_name: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """Validate + store a financial document; processing happens separately."""
    service = IngestionService(db)
    data = file.file.read()
    document, _duplicate = service.upload_document(
        filename=file.filename or "unnamed",
        data=data,
        storage=DocumentStorageService(get_storage()),
        company_id=company_id,
        document_type=document_type,
        source_url=source_url,
        source_name=source_name,
    )
    return document


@router.post("/{document_id}/process", status_code=status.HTTP_202_ACCEPTED)
def process_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    force: bool = Query(default=False, description="Reprocess even if already processed"),
    db: Session = Depends(get_db),
):
    """Queue full pipeline processing (runs in the background)."""
    service = IngestionService(db)
    service.mark_queued(document_id)
    background_tasks.add_task(run_ingestion, document_id, force)
    return {"document_id": document_id, "status": "queued"}


@router.get("/{document_id}/status")
def get_document_status(document_id: int, service=Depends(_service)):
    document = service.get_document(document_id)
    return {
        "document_id": document.id,
        "status": document.processing_status,
        "page_count": document.page_count,
        "processing_started_at": document.processing_started_at,
        "processing_completed_at": document.processing_completed_at,
        "error": document.processing_error,
    }


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(payload: DocumentCreate, service=Depends(_service)):
    return service.create_document(payload)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, service=Depends(_service)):
    return service.get_document(document_id)


@router.get("/{document_id}/pages", response_model=list[DocumentPageRead])
def list_pages(document_id: int, service=Depends(_service)):
    return service.list_pages(document_id)


@router.post(
    "/{document_id}/pages",
    response_model=DocumentPageRead,
    status_code=status.HTTP_201_CREATED,
)
def add_page(
    document_id: int, payload: DocumentPageCreate, service=Depends(_service)
):
    return service.add_page(document_id, payload)


@router.get("/{document_id}/sections", response_model=list[DocumentSectionRead])
def list_sections(document_id: int, service=Depends(_service)):
    return service.list_sections(document_id)


@router.post(
    "/{document_id}/sections",
    response_model=DocumentSectionRead,
    status_code=status.HTTP_201_CREATED,
)
def add_section(
    document_id: int, payload: DocumentSectionCreate, service=Depends(_service)
):
    return service.add_section(document_id, payload)


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkRead])
def list_chunks(
    document_id: int,
    chunk_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service=Depends(_service),
):
    service.get_document(document_id)
    return service.chunks.list_for_document(
        document_id, chunk_type=chunk_type, limit=limit, offset=offset
    )


@router.post(
    "/{document_id}/chunks",
    response_model=DocumentChunkRead,
    status_code=status.HTTP_201_CREATED,
)
def add_chunk(
    document_id: int, payload: DocumentChunkCreate, service=Depends(_service)
):
    return service.add_chunk(document_id, payload)


@router.get("/{document_id}/tables", response_model=list[FinancialTableRead])
def list_tables(document_id: int, service=Depends(_service)):
    return service.list_tables(document_id)


@router.post(
    "/{document_id}/tables",
    response_model=FinancialTableRead,
    status_code=status.HTTP_201_CREATED,
)
def add_table(
    document_id: int, payload: FinancialTableCreate, service=Depends(_service)
):
    return service.add_table(document_id, payload)


@router.get("/{document_id}/tables/{table_id}", response_model=FinancialTableRead)
def get_table(document_id: int, table_id: int, service=Depends(_service)):
    return service.get_table(document_id, table_id)


# ── company-scoped document listing (kept with documents for clarity) ──

company_docs_router = APIRouter(prefix="/companies", tags=["documents"])


@company_docs_router.get(
    "/{company_id}/documents", response_model=list[DocumentRead]
)
def list_company_documents(
    company_id: int,
    document_type: str | None = Query(default=None),
    fiscal_year: int | None = Query(default=None, ge=1900, le=2100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    service = DocumentService(db)
    return service.list_documents_for_company(
        company_id,
        document_type=document_type,
        fiscal_year=fiscal_year,
        limit=limit,
        offset=offset,
    )
