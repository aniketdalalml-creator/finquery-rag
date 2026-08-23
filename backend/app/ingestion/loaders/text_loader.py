"""Plain-text loader — one file, one page."""

from __future__ import annotations

from app.ingestion.loaders.base import BaseLoader, LoaderError, RawDocument, RawPage


class TextLoader(BaseLoader):
    supported_extensions = frozenset({"txt", "text", "md"})

    def load(self, data: bytes, filename: str) -> RawDocument:
        if not data:
            raise LoaderError(f"Empty text payload: {filename!r}")
        for encoding in ("utf-8", "cp1252", "latin-1"):
            try:
                text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:  # pragma: no cover - latin-1 never fails
            raise LoaderError(f"Cannot decode text file: {filename!r}")

        return RawDocument(
            filename=filename,
            format="txt",
            pages=[RawPage(page_number=1, text=text,
                           metadata={"char_count": len(text)})],
            metadata={"encoding": encoding},
        )
