"""Section detection stage."""

from __future__ import annotations

from app.ingestion.sectioning.detector import DetectedSection, SectionDetector
from app.ingestion.sectioning.patterns import SECTION_PATTERNS

__all__ = ["DetectedSection", "SectionDetector", "SECTION_PATTERNS"]
