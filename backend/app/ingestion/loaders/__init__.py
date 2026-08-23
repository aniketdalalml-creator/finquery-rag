"""Document loaders: raw bytes → RawDocument with page boundaries.

Loaders never parse structure beyond page extraction — cleaning, sections,
tables and metrics are downstream pipeline stages.
"""

from __future__ import annotations

from app.ingestion.loaders.base import (
    BaseLoader,
    LoaderError,
    RawDocument,
    RawPage,
    UnsupportedFormatError,
)
from app.ingestion.loaders.registry import get_loader

__all__ = [
    "BaseLoader",
    "LoaderError",
    "RawDocument",
    "RawPage",
    "UnsupportedFormatError",
    "get_loader",
]
