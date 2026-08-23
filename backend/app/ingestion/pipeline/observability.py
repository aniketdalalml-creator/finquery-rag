"""Lightweight in-process ingestion metrics.

Counters only — no external observability platform. Thread-safety relies
on the GIL; increments are single dict operations.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class IngestionStats:
    documents_processed: int = 0
    documents_partially_processed: int = 0
    documents_failed: int = 0
    pages_processed: int = 0
    tables_extracted: int = 0
    metrics_extracted: int = 0
    chunks_created: int = 0
    total_processing_duration_ms: float = 0.0
    started_at: float = field(default_factory=time.time)

    def snapshot(self) -> dict:
        return {
            "documents_processed": self.documents_processed,
            "documents_partially_processed": self.documents_partially_processed,
            "documents_failed": self.documents_failed,
            "pages_processed": self.pages_processed,
            "tables_extracted": self.tables_extracted,
            "metrics_extracted": self.metrics_extracted,
            "chunks_created": self.chunks_created,
            "total_processing_duration_ms": round(self.total_processing_duration_ms, 1),
            "uptime_seconds": round(time.time() - self.started_at, 1),
        }


class _StatsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stats = IngestionStats()

    def snapshot(self) -> dict:
        with self._lock:
            return self._stats.snapshot()

    def record_document(self, status: str, duration_ms: float) -> None:
        with self._lock:
            if status == "processed":
                self._stats.documents_processed += 1
            elif status == "partially_processed":
                self._stats.documents_partially_processed += 1
            elif status == "failed":
                self._stats.documents_failed += 1
            self._stats.total_processing_duration_ms += duration_ms

    def bump(self, **counts: int) -> None:
        with self._lock:
            for key, value in counts.items():
                setattr(self._stats, key, getattr(self._stats, key, 0) + value)


_stats = _StatsRegistry()


def get_ingestion_stats() -> _StatsRegistry:
    return _stats
