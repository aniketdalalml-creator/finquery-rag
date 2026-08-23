"""OCRProvider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class OCRError(Exception):
    """Raised when an OCR provider fails on a page."""


@dataclass
class OCRResult:
    text: str
    confidence: float | None  # provider-reported mean confidence, if any
    engine: str


class OCRProvider(ABC):
    name: str = "ocr"

    @abstractmethod
    def is_available(self) -> bool:
        """Whether this provider can run in the current environment."""

    @abstractmethod
    def recognize_page(self, pdf_bytes: bytes, page_number: int) -> OCRResult:
        """Run OCR on one PDF page (1-based). Raises OCRError on failure."""
