"""Finance document ingestion & parsing pipeline (Prompt 3).

Stages: validate → load → ocr → clean → section_detection →
table_extraction → metadata_extraction → chunking → metric_extraction →
persist. Each stage is isolated and independently testable.
"""

from __future__ import annotations

from app.ingestion.pipeline import (
    DocumentIngestionPipeline,
    IngestionResult,
    PipelineError,
    StageResult,
    get_ingestion_stats,
)

__all__ = [
    "DocumentIngestionPipeline",
    "IngestionResult",
    "StageResult",
    "PipelineError",
    "get_ingestion_stats",
]
