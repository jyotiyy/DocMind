"""Text cleaning, normalization, and section-header detection utilities."""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"[ \t\u00a0]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_HYPHENATED_LINEBREAK_RE = re.compile(r"(\w)-\n(\w)")
_SECTION_HEADER_RE = re.compile(
    r"^(?:[0-9]+(?:\.[0-9]+)*\s+)?[A-Z][A-Za-z0-9 ,:\-]{2,80}$"
)


def clean_text(text: str) -> str:
    """Normalize whitespace, unicode, and hyphenation artifacts from PDF text."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = _HYPHENATED_LINEBREAK_RE.sub(r"\1\2", text)
    text = _WHITESPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def looks_like_section_header(line: str) -> bool:
    """Heuristically determine whether a line of text is a section header.

    Headers are typically short, title-cased or numbered, and do not end
    with terminal punctuation such as a period.
    """
    stripped = line.strip()
    if not stripped or len(stripped) > 90:
        return False
    if stripped.endswith((".", ",", ";")):
        return False
    word_count = len(stripped.split())
    if word_count > 12:
        return False
    return bool(_SECTION_HEADER_RE.match(stripped))


def extract_last_section_header(text: str) -> str | None:
    """Scan text top-to-bottom and return the most recent section header found."""
    header: str | None = None
    for line in text.splitlines():
        if looks_like_section_header(line):
            header = line.strip()
    return header


def truncate(text: str, max_chars: int) -> str:
    """Truncate text to a maximum number of characters, on a word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(" ", 1)[0]
    return f"{truncated}..."


def count_words(text: str) -> int:
    """Return the number of whitespace-delimited words in a string."""
    return len(text.split())
