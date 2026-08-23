"""SectionDetector — finds headings and builds a section tree.

Headings are lines that either match a known financial-section pattern or
look like short title-case headings. Every detected heading becomes a
section; unknown headings map to type "Other". Hierarchy: a top-level
heading starts a new root; non-top-level known headings nest under the
current root.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.ingestion.sectioning.patterns import SECTION_PATTERNS

# Generic heading heuristics (used when no known pattern matches).
_MAX_HEADING_WORDS = 14
_TITLE_CASE_LINE = re.compile(r"^[A-Z0-9][A-Za-z0-9,&/()'’\-\s]{2,120}$")
_ALL_CAPS_LINE = re.compile(r"^[A-Z0-9][A-Z0-9,&/()\-\s]{2,120}$")
_NUMBER_PREFIX = re.compile(r"^\d+(\.\d+)*[.)]?\s+\S")


@dataclass
class DetectedSection:
    title: str
    section_type: str
    page_start: int
    page_end: int | None = None
    parent: "DetectedSection | None" = None
    children: list["DetectedSection"] = field(default_factory=list)
    is_known_heading: bool = False

    @property
    def flat(self) -> list["DetectedSection"]:
        """This section and all descendants, document order."""
        out = [self]
        for child in self.children:
            out.extend(child.flat)
        return out

    def path_to_root(self) -> list["DetectedSection"]:
        """Ancestors from this node upward."""
        node, path = self, []
        while node is not None:
            path.append(node)
            node = node.parent
        return path


def _match_known(line: str) -> tuple[str, str, bool] | None:
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return None
    for pattern, title, section_type, top_level in SECTION_PATTERNS:
        if pattern.match(stripped):
            return title, section_type, top_level
    return None


def _looks_like_generic_heading(prev_line_blank: bool, line: str, next_blank: bool) -> bool:
    """Conservative generic-heading heuristic."""
    if not prev_line_blank or not next_blank:
        return False
    stripped = line.strip()
    words = stripped.split()
    if not 2 <= len(words) <= _MAX_HEADING_WORDS:
        return False
    if _NUMBER_PREFIX.match(stripped):
        return True
    if _ALL_CAPS_LINE.match(stripped) and any(c.isalpha() for c in stripped):
        return True
    if _TITLE_CASE_LINE.match(stripped) and stripped[0].isupper():
        # Require most words capitalized to avoid false positives on
        # ordinary sentence fragments.
        capitalized = sum(1 for w in words if w[:1].isupper())
        return capitalized / len(words) >= 0.6
    return False


class SectionDetector:
    def __init__(self, detect_generic_headings: bool = True) -> None:
        self._detect_generic = detect_generic_headings

    def detect(self, cleaned_pages: dict[int, str]) -> list[DetectedSection]:
        """Detect sections across pages; returns roots in document order."""
        roots: list[DetectedSection] = []
        current_root: DetectedSection | None = None
        current_child: DetectedSection | None = None
        # Sections awaiting their end-page assignment.
        open_sections: list[DetectedSection] = []

        def close_open(upto_page_exclusive: int, up_to_line_page: int | None = None):
            for sec in open_sections:
                if sec.page_end is None:
                    sec.page_end = upto_page_exclusive

        for page_number in sorted(cleaned_pages):
            lines = cleaned_pages[page_number].splitlines()
            for index, line in enumerate(lines):
                if not line.strip():
                    continue
                prev_blank = index == 0 or not lines[index - 1].strip()
                next_blank = index == len(lines) - 1 or not lines[index + 1].strip()

                match = _match_known(line)
                is_generic = (
                    match is None
                    and self._detect_generic
                    and _looks_like_generic_heading(prev_blank, line, next_blank)
                )
                if match is None and not is_generic:
                    continue

                if match is not None:
                    title, section_type, top_level = match
                    known = True
                else:
                    title, section_type, top_level = line.strip(), "Other", False
                    known = False

                close_open(page_number)

                new_section = DetectedSection(
                    title=title,
                    section_type=section_type,
                    page_start=page_number,
                    is_known_heading=known,
                )
                if top_level or current_root is None:
                    roots.append(new_section)
                    current_root = new_section
                    current_child = None
                else:
                    target = current_child or current_root
                    new_section.parent = target
                    target.children.append(new_section)
                    current_child = new_section
                open_sections.append(new_section)

        last_page = max(cleaned_pages, default=0)
        close_open(last_page)
        return roots
