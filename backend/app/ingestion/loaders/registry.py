"""Loader registry — resolves the right loader for a filename.

New formats plug in by adding a BaseLoader subclass to DEFAULT_LOADERS.
"""

from __future__ import annotations

from pathlib import Path

from app.ingestion.loaders.base import (
    BaseLoader,
    UnsupportedFormatError,
)
from app.ingestion.loaders.html_loader import HTMLLoader
from app.ingestion.loaders.pdf_loader import PDFLoader
from app.ingestion.loaders.text_loader import TextLoader

DEFAULT_LOADERS: tuple[BaseLoader, ...] = (PDFLoader(), HTMLLoader(), TextLoader())


def get_loader(filename: str, loaders: tuple[BaseLoader, ...] | None = None) -> BaseLoader:
    """Return the loader handling `filename`, or raise UnsupportedFormatError."""
    suffix = Path(filename).suffix.lower().lstrip(".")
    for loader in loaders or DEFAULT_LOADERS:
        if loader.matches(filename):
            return loader
    supported = sorted(ext for l in (loaders or DEFAULT_LOADERS) for ext in l.supported_extensions)
    raise UnsupportedFormatError(
        f"Unsupported file format {suffix!r}. Supported: {supported}"
    )
