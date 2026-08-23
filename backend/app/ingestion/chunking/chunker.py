"""FinanceAwareChunker — section → paragraph/table → semantic chunk.

Boundaries respect sections, paragraphs and tables. Each planned chunk
carries its page span so provenance (chunk → page → document) survives.
Token counts use tiktoken (cl100k_base); the encoder is loaded lazily and
falls back to a chars/4 estimate if unavailable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.core.config import config

logger = logging.getLogger(__name__)

_ENCODER = None


def count_tokens(text: str) -> int:
    global _ENCODER
    if _ENCODER is None:
        try:
            import tiktoken

            _ENCODER = tiktoken.get_encoding("cl100k_base")
        except Exception:  # pragma: no cover - offline environments
            _ENCODER = False
    if _ENCODER is False:
        return max(1, len(text) // 4)
    return len(_ENCODER.encode(text))


@dataclass
class PlannedChunk:
    text: str
    chunk_type: str  # text | table | financial_metric | table_row | section_summary
    page_start: int
    page_end: int
    token_count: int
    section_path: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    chunk_index: int = 0


@dataclass
class _ParagraphBlock:
    text: str
    pages: set[int]
    is_table: bool = False
    table_ref: tuple[int, int] | None = None  # (page_number, position)


class FinanceAwareChunker:
    def __init__(self, target_tokens: int | None = None, overlap_sentences: int = 1) -> None:
        self._target = target_tokens or config.CHUNK_SIZE
        self._overlap = overlap_sentences

    def build_chunks(
        self,
        cleaned_pages: dict[int, str],
        sections: list[dict],
        tables: list[dict] | None = None,
    ) -> list[PlannedChunk]:
        """Build chunks.

        `sections`: [{"title", "section_type", "page_start", "page_end",
                      "path": [titles], "lines": [(page_number, line)]}]
        — produced by the pipeline from detector output + cleaned pages.

        `tables`: [{"page_number", "headers", "rows", "raw_text", ...}]
        """
        tables_by_page: dict[int, list[dict]] = {}
        for table in tables or []:
            tables_by_page.setdefault(table["page_number"], []).append(table)

        chunks: list[PlannedChunk] = []
        for section in sections:
            blocks = self._blocks_from_lines(section.get("lines") or [], tables_by_page)
            section_chunks = self._chunk_blocks(blocks, section)
            chunks.extend(section_chunks)

        # Pages outside every detected section still deserve chunks.
        covered_pages: set[int] = set()
        for section in sections:
            covered_pages.update(
                range(section["page_start"], (section["page_end"] or section["page_start"]) + 1)
            )
        uncovered = [p for p in sorted(cleaned_pages) if p not in covered_pages]
        if uncovered:
            lines = []
            for page_number in uncovered:
                for line in cleaned_pages[page_number].splitlines():
                    if line.strip():
                        lines.append((page_number, line))
            if lines:
                fallback_section = {
                    "title": "(unsectioned content)",
                    "section_type": "Other",
                    "path": [],
                    "lines": lines,
                }
                chunks.extend(self._chunk_blocks(self._blocks_from_lines(lines, tables_by_page), fallback_section))

        # Re-number globally in document order.
        for index, chunk in enumerate(chunks):
            chunk.chunk_index = index
        return chunks

    def _blocks_from_lines(
        self, lines: list[tuple[int, str]], tables_by_page: dict[int, list[dict]]
    ) -> list[_ParagraphBlock]:
        """Group lines into paragraph blocks; emit table blocks separately."""
        blocks: list[_ParagraphBlock] = []
        buffer: list[str] = []
        buffer_pages: set[int] = set()
        emitted_table_keys: set[tuple[int, int]] = set()

        def flush():
            nonlocal buffer, buffer_pages
            if buffer:
                text = "\n".join(buffer).strip()
                if text:
                    blocks.append(_ParagraphBlock(text=text, pages=set(buffer_pages)))
            buffer, buffer_pages = [], set()

        for page_number, line in lines:
            if not line.strip():
                flush()
                continue
            buffer.append(line)
            buffer_pages.add(page_number)
            if len(" ".join(buffer)) >= 1200:  # hard cap per paragraph block
                flush()

        flush()

        # Insert a table block after the paragraph block containing its page.
        result: list[_ParagraphBlock] = []
        inserted_pages: set[int] = set()
        for block in blocks:
            result.append(block)
            for page in block.pages:
                for position, table in enumerate(tables_by_page.get(page, [])):
                    key = (page, position)
                    if key in emitted_table_keys:
                        continue
                    result.append(
                        _ParagraphBlock(
                            text=self._render_table(table),
                            pages={page},
                            is_table=True,
                            table_ref=key,
                        )
                    )
                    emitted_table_keys.add(key)
                    inserted_pages.add(page)
        # Tables on pages with no paragraph blocks.
        for page, tables_on_page in sorted(tables_by_page.items()):
            for position, table in enumerate(tables_on_page):
                if (page, position) not in emitted_table_keys:
                    result.append(
                        _ParagraphBlock(
                            text=self._render_table(table),
                            pages={page},
                            is_table=True,
                            table_ref=(page, position),
                        )
                    )
                    emitted_table_keys.add((page, position))
        return result

    @staticmethod
    def _render_table(table: dict) -> str:
        headers = table.get("headers") or []
        rows = table.get("rows") or []
        title = table.get("title") or "Table"
        lines = [f"[TABLE] {title}"]
        if headers:
            lines.append(" | ".join(str(h) for h in headers))
        for row in rows[:40]:  # safety bound; huge tables stay bounded
            cells = row.get("cells") if isinstance(row, dict) else row
            lines.append(" | ".join(str(c) for c in cells))
        return "\n".join(lines)

    def _chunk_blocks(self, blocks: list[_ParagraphBlock], section: dict) -> list[PlannedChunk]:
        chunks: list[PlannedChunk] = []
        pack: list[_ParagraphBlock] = []
        pack_tokens = 0

        def flush_pack():
            nonlocal pack, pack_tokens
            if not pack:
                return
            text = "\n\n".join(block.text for block in pack)
            pages: set[int] = set()
            for block in pack:
                pages.update(block.pages)
            path = section.get("path") or ([section["title"]] if section.get("title") else [])
            chunks.append(
                PlannedChunk(
                    text=text,
                    # Tables are flushed separately, so packed blocks are text.
                    chunk_type="text",
                    page_start=min(pages),
                    page_end=max(pages),
                    token_count=count_tokens(text),
                    section_path=[str(p) for p in path],
                    metadata={
                        "section_title": section.get("title"),
                        "section_type": section.get("section_type"),
                    },
                )
            )
            pack, pack_tokens = [], 0

        for block in blocks:
            block_tokens = count_tokens(block.text)
            # Tables never merge with other blocks.
            if block.is_table:
                flush_pack()
                chunks.extend(
                    self._single_block_chunks(block, section, force_table_type=True)
                )
                continue
            if block_tokens > self._target:
                flush_pack()
                chunks.extend(self._split_large_block(block, section))
                continue
            if pack_tokens + block_tokens > self._target:
                flush_pack()
            pack.append(block)
            pack_tokens += block_tokens
        flush_pack()
        return chunks

    def _single_block_chunks(
        self, block: _ParagraphBlock, section: dict, force_table_type: bool = False
    ) -> list[PlannedChunk]:
        path = section.get("path") or ([section["title"]] if section.get("title") else [])
        chunk_type = "table" if (block.is_table or force_table_type) else "text"
        meta = {
            "section_title": section.get("title"),
            "section_type": section.get("section_type"),
        }
        if block.table_ref is not None:
            meta["table_page"] = block.table_ref[0]
            meta["table_pos"] = block.table_ref[1]
        return [
            PlannedChunk(
                text=block.text,
                chunk_type=chunk_type,
                page_start=min(block.pages),
                page_end=max(block.pages),
                token_count=count_tokens(block.text),
                section_path=[str(p) for p in path],
                metadata=meta,
            )
        ]

    def _split_large_block(self, block: _ParagraphBlock, section: dict) -> list[PlannedChunk]:
        """Split oversized paragraphs on sentence boundaries."""
        sentences = _split_sentences(block.text)
        out: list[PlannedChunk] = []
        current: list[str] = []
        current_tokens = 0
        for sentence in sentences:
            tokens = count_tokens(sentence)
            if current and current_tokens + tokens > self._target:
                out.append(self._sentence_chunk(current, block, section))
                # carry-over overlap
                tail = current[-self._overlap:] if self._overlap else []
                current = [*tail, sentence]
                current_tokens = sum(count_tokens(s) for s in current)
            else:
                current.append(sentence)
                current_tokens += tokens
        if current:
            out.append(self._sentence_chunk(current, block, section))
        return out

    def _sentence_chunk(
        self, sentences: list[str], block: _ParagraphBlock, section: dict,
    ) -> PlannedChunk:
        text = " ".join(sentences)
        path = section.get("path") or ([section["title"]] if section.get("title") else [])
        return PlannedChunk(
            text=text,
            chunk_type="table" if block.is_table else "text",
            page_start=min(block.pages),
            page_end=max(block.pages),
            token_count=count_tokens(text),
            section_path=[str(p) for p in path],
            metadata={
                "section_title": section.get("title"),
                "section_type": section.get("section_type"),
            },
        )


def _split_sentences(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    for token in text.replace("! ", "!|").replace("? ", "?|").split("|"):
        sub = token.split(". ")
        for piece_index, piece in enumerate(sub):
            if piece_index < len(sub) - 1:
                current.append(piece.rstrip(".") + ".")
                parts.append(" ".join(current))
                current = []
            elif piece.strip():
                current.append(piece)
    if current:
        parts.append(" ".join(current))
    return [p.strip() for p in parts if p.strip()]
