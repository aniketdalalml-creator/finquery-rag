"""OCR abstraction.

The pipeline only invokes OCR when a page looks image-only (see loaders).
Providers plug in behind OCRProvider; the local Tesseract provider degrades
gracefully when the binary is missing so ingestion never hard-fails on it.
"""

from __future__ import annotations

from app.ingestion.ocr.base import OCRProvider, OCRError
from app.ingestion.ocr.local import LocalOCRProvider, get_ocr_provider

__all__ = ["OCRProvider", "OCRError", "LocalOCRProvider", "get_ocr_provider"]
