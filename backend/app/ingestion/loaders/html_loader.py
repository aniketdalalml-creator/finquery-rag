"""HTML loader — converts HTML to text using the stdlib (no extra deps).

An HTML document is treated as a single page; `<title>` is surfaced in
metadata. Script/style content and invisible elements are dropped.
"""

from __future__ import annotations

from html.parser import HTMLParser

from app.ingestion.loaders.base import BaseLoader, LoaderError, RawDocument, RawPage

# Elements whose entire subtree contributes no visible text.
_SKIPPED_ELEMENTS = frozenset(
    {"script", "style", "head", "noscript", "template", "svg", "iframe"}
)
# Block-level elements produce line breaks when they end.
_BLOCK_ELEMENTS = frozenset(
    {
        "p", "div", "section", "article", "li", "tr", "table", "h1", "h2",
        "h3", "h4", "h5", "h6", "br", "hr", "blockquote", "figcaption", "dd",
        "dt", "pre",
    }
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0
        self.title: str | None = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in _SKIPPED_ELEMENTS:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in _SKIPPED_ELEMENTS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in _BLOCK_ELEMENTS:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data.strip()
            return
        if self._skip_depth == 0 and data.strip():
            self._chunks.append(data)

    @property
    def text(self) -> str:
        raw = "".join(self._chunks)
        lines = [" ".join(line.split()) for line in raw.splitlines()]
        return "\n".join(line for line in lines if line)


class HTMLLoader(BaseLoader):
    supported_extensions = frozenset({"html", "htm"})

    def load(self, data: bytes, filename: str) -> RawDocument:
        if not data:
            raise LoaderError(f"Empty HTML payload: {filename!r}")
        for encoding in ("utf-8", "cp1252", "latin-1"):
            try:
                html_text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:  # pragma: no cover - latin-1 never fails
            raise LoaderError(f"Cannot decode HTML: {filename!r}")

        extractor = _TextExtractor()
        try:
            extractor.feed(html_text)
            extractor.close()
        except Exception as exc:
            raise LoaderError(f"Cannot parse HTML {filename!r}: {exc}") from exc

        return RawDocument(
            filename=filename,
            format="html",
            pages=[RawPage(page_number=1, text=extractor.text,
                           metadata={"char_count": len(extractor.text)})],
            metadata={"title": extractor.title, "encoding": encoding},
        )
