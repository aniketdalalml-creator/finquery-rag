"""PDF loader — page-by-page text extraction via pypdf.

- preserves page boundaries and 1-based page numbers
- flags pages whose extracted text is below a threshold as OCR candidates
- records extraction warnings instead of silently discarding failures
"""

from __future__ import annotations

import io
import logging

from app.core.config import config
from app.ingestion.loaders.base import (
    BaseLoader,
    LoaderError,
    RawDocument,
    RawPage,
)

logger = logging.getLogger(__name__)

# Pages with fewer characters than this are flagged needs_ocr (the pipeline's
# OCR stage decides whether to actually run OCR).
OCR_CANDIDATE_CHARS = 32


class PDFLoader(BaseLoader):
    supported_extensions = frozenset({"pdf"})

    def load(self, data: bytes, filename: str) -> RawDocument:
        from pypdf import PdfReader

        if not data:
            raise LoaderError(f"Empty PDF payload: {filename!r}")

        try:
            reader = PdfReader(io.BytesIO(data), strict=False)
        except Exception as exc:  # pypdf parse failure
            raise LoaderError(f"Cannot read PDF {filename!r}: {exc}") from exc

        if reader.is_encrypted:
            try:
                if not reader.decrypt(""):
                    raise LoaderError(
                        f"Password-protected PDF cannot be opened: {filename!r}"
                    )
            except LoaderError:
                raise
            except Exception as exc:
                raise LoaderError(
                    f"Encrypted PDF could not be decrypted: {filename!r}: {exc}"
                ) from exc

        pages: list[RawPage] = []
        for index, pdf_page in enumerate(reader.pages):
            page_number = index + 1
            text, warnings, meta = self._extract_page(pdf_page)
            pages.append(
                RawPage(
                    page_number=page_number,
                    text=text,
                    metadata=meta,
                    needs_ocr=len(text.strip()) < OCR_CANDIDATE_CHARS,
                )
            )
            for warning in warnings:
                logger.warning(
                    "pdf extraction warning file=%s page=%d: %s",
                    filename,
                    page_number,
                    warning,
                )

        return RawDocument(
            filename=filename,
            format="pdf",
            pages=pages,
            metadata={
                "page_count": len(pages),
                "ocr_candidate_pages": [p.page_number for p in pages if p.needs_ocr],
                "min_text_chars": getattr(config, "OCR_MIN_TEXT_CHARS", 0) or None,
            },
        )

    @staticmethod
    def _extract_page(pdf_page) -> tuple[str, list[str], dict]:
        """Extract one page; try layout mode first, fall back to plain mode."""
        warnings: list[str] = []
        # Prefer layout mode (better multi-column fidelity); some malformed
        # PDFs only extract in plain mode, so degrade gracefully.
        text = ""
        used_modes: list[str] = []
        try:
            text = pdf_page.extract_text(extraction_mode="layout") or ""
            used_modes.append("layout")
        except TypeError:
            pass  # older pypdf without extraction_mode
        except Exception as exc:
            warnings.append(f"layout-mode extraction failed: {type(exc).__name__}")

        if len(text.strip()) == 0:
            try:
                plain = pdf_page.extract_text() or ""
                if plain.strip():
                    text = plain
                    used_modes.append("plain")
            except Exception as exc:
                warnings.append(f"plain extraction failed: {type(exc).__name__}")
                text = ""

        meta = {
            "extraction_modes": used_modes,
            "char_count": len(text),
        }
        return text, warnings, meta
