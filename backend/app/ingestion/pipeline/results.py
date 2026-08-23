"""Stage results and the ingestion result envelope."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

# Stage outcomes.
SUCCESS = "success"
SKIPPED = "skipped"
FAILED = "failed"
PARTIAL = "partial"


@dataclass
class StageResult:
    stage: str
    status: str
    duration_ms: float
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
            "details": self.details,
        }


@dataclass
class IngestionResult:
    document_id: int | None
    status: str  # processed | partially_processed | failed
    stages: list[StageResult] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, stage_name: str):
        """Context manager recording a StageResult for `stage_name`."""
        return _StageRecorder(self, stage_name)

    @property
    def ok_stages(self) -> list[StageResult]:
        return [s for s in self.stages if s.status in (SUCCESS, SKIPPED)]


class _StageRecorder:
    def __init__(self, result: IngestionResult, stage_name: str) -> None:
        self._result = result
        self.stage_name = stage_name
        self._start = 0.0

    def __enter__(self) -> "_StageRecorder":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        duration = (time.perf_counter() - self._start) * 1000
        if exc_type is None:
            self._result.stages.append(
                StageResult(stage=self.stage_name, status=SUCCESS, duration_ms=duration)
            )
            return False
        if isinstance(exc, _StagePartial):
            self._result.stages.append(
                StageResult(
                    stage=self.stage_name,
                    status=PARTIAL,
                    duration_ms=duration,
                    error=str(exc),
                    details=exc.details,
                )
            )
            return True  # swallow: pipeline continues after partial failures
        if isinstance(exc, _StageSkip):
            self._result.stages.append(
                StageResult(
                    stage=self.stage_name,
                    status=SKIPPED,
                    duration_ms=duration,
                    error=None,
                    details={"reason": str(exc)},
                )
            )
            return True  # swallow: skip is not an error
        self._result.stages.append(
            StageResult(
                stage=self.stage_name,
                status=FAILED,
                duration_ms=duration,
                error=f"{exc_type.__name__}: {exc}",
            )
        )
        return True  # orchestrator inspects recorded failure


class _StagePartial(Exception):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class _StageSkip(Exception):
    pass


def stage_partial(message: str, details: dict | None = None) -> _StagePartial:
    return _StagePartial(message, details)


def stage_skip(reason: str) -> _StageSkip:
    return _StageSkip(reason)
