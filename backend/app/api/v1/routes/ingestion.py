"""Ingestion observability endpoints (lightweight counters)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ingestion.pipeline import get_ingestion_stats

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.get("/stats")
def ingestion_stats(db: Session = Depends(get_db)):
    return get_ingestion_stats().snapshot()
