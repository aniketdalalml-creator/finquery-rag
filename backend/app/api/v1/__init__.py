"""Versioned API v1 router assembly."""

from fastapi import APIRouter

from app.api.v1.routes import companies, documents, ingestion, metrics, rag, stats

v1_router = APIRouter()
v1_router.include_router(companies.router)
v1_router.include_router(documents.router)
v1_router.include_router(documents.company_docs_router)
v1_router.include_router(metrics.router)
v1_router.include_router(ingestion.router)
v1_router.include_router(rag.router)
v1_router.include_router(stats.router)
