"""Pipeline orchestration: stage runner, results, observability."""

from __future__ import annotations

from app.ingestion.pipeline.observability import get_ingestion_stats
from app.ingestion.pipeline.orchestrator import DocumentIngestionPipeline, PipelineError
from app.ingestion.pipeline.results import IngestionResult, StageResult

__all__ = [
    "DocumentIngestionPipeline",
    "PipelineError",
    "IngestionResult",
    "StageResult",
    "get_ingestion_stats",
]
