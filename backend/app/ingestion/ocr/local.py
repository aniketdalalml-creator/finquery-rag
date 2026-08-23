"""LocalOCRProvider — Tesseract via pytesseract, if installed.

Rendered page images are produced by pypdf (no poppler dependency).
When Tesseract is not installed the provider reports unavailable and the
pipeline records the page as needing OCR instead of failing ingestion.
"""

from __future__ import annotations

import io
import logging

from app.ingestion.ocr.base import OCRError, OCRProvider, OCRResult

logger = logging.getLogger(__name__)


class LocalOCRProvider(OCRProvider):
    name = "tesseract"

    def __init__(self, language: str = "eng") -> None:
        self._language = language
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is None:
            try:
                import pytesseract  # noqa: F401

                pytesseract.get_tesseract_version()
                self._available = True
            except Exception:
                logger.info(
                    "Tesseract OCR not available; image-only pages will be "
                    "recorded as needs_ocr without text"
                )
                self._available = False
        return self._available

    def recognize_page(self, pdf_bytes: bytes, page_number: int) -> OCRResult:
        try:
            import pytesseract
            from PIL import Image
            from pypdf import PdfReader
        except ImportError as exc:
            raise OCRError(f"OCR dependencies missing: {exc}") from exc

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes), strict=False)
            pdf_page = reader.pages[page_number - 1]
            images = pdf_page.images
            if not images:
                # No embedded raster image — render fallback is not available
                # without extra binaries; report a clear failure.
                raise OCRError(
                    f"Page {page_number} has no embedded image to OCR and no "
                    f"rasterizer is configured"
                )
            image = Image.open(io.BytesIO(images[0].data))
            text = pytesseract.image_to_string(image, lang=self._language)
            confidence = None
            return OCRResult(
                text=text or "",
                confidence=confidence,
                engine=self.name,
            )
        except OCRError:
            raise
        except Exception as exc:
            raise OCRError(f"Tesseract OCR failed on page {page_number}: {exc}") from exc


def get_ocr_provider() -> OCRProvider | None:
    """Return the configured provider, or None when OCR cannot run."""
    provider = LocalOCRProvider()
    return provider if provider.is_available() else None
