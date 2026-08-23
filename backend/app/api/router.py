"""HTTP route modules."""

from fastapi import APIRouter

from app.api.routes import documents, health, ingest, query
from app.api.v1.routes import stats

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(query.router, tags=["chat"])
api_router.include_router(ingest.router, tags=["ingest"])
api_router.include_router(documents.router, tags=["documents"])
# Dashboard counters are also exposed un-versioned so the Vite dev proxy
# (/api -> backend root, prefix stripped) reaches them like /query or /ingest.
api_router.include_router(stats.router, tags=["stats"])
