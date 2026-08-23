"""Loader abstraction: `load(source) -> RawDocument`.

A RawDocument preserves page boundaries and per-page extraction details.
Nothing is merged into one giant string — downstream stages rely on pages
for provenance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


class LoaderError(Exception):
    """Raised when a document cannot be loaded at all."""


class UnsupportedFormatError(LoaderError):
    """Raised when no loader exists for the given format."""


@dataclass
class RawPage:
    """One physical page as extracted by a loader."""

    page_number: int  # 1-based
    text: str = ""
    # Details recorded for auditability (char count, warnings, engine...).
    metadata: dict = field(default_factory=dict)
    needs_ocr: bool = False  # loader suspects image-only / too-little text

    @property
    def char_count(self) -> int:
        return len(self.text)


@dataclass
class RawDocument:
    """Raw, page-preserving result of loading a source file."""

    filename: str
    format: str  # "pdf" | "html" | "txt"
    pages: list[RawPage] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)


class BaseLoader(ABC):
    """Interface every loader implements. `source` is raw bytes + name."""

    supported_extensions: frozenset[str] = frozenset()

    @abstractmethod
    def load(self, data: bytes, filename: str) -> RawDocument:
        """Load raw bytes into a RawDocument. Raises LoaderError on failure."""

    def matches(self, filename: str) -> bool:
        suffix = Path(filename).suffix.lower().lstrip(".")
        return suffix in self.supported_extensions
