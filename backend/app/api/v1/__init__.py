"""Versioned API v1 router assembly."""

from fastapi import APIRouter, Depends

from app.api.v1.routes import auth, companies, documents, ingestion, metrics, rag, stats
from app.security import get_current_user

v1_router = APIRouter()
v1_router.include_router(auth.router)

protected = APIRouter(dependencies=[Depends(get_current_user)])
protected.include_router(companies.router)
protected.include_router(documents.router)
protected.include_router(documents.company_docs_router)
protected.include_router(metrics.router)
protected.include_router(ingestion.router)
protected.include_router(rag.router)
protected.include_router(stats.router)
v1_router.include_router(protected)
