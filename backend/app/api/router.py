"""HTTP route modules."""

from fastapi import APIRouter

from app.api.routes import documents, health, ingest, query

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(query.router, tags=["chat"])
api_router.include_router(ingest.router, tags=["ingest"])
api_router.include_router(documents.router, tags=["documents"])
