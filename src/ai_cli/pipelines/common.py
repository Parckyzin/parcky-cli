from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

T = TypeVar("T")


def stable_sorted(
    items: Iterable[T], *, key: Callable[[T], object] | None = None
) -> list[T]:
    """Return a stably sorted list."""
    return sorted(items, key=key)


def dedupe_preserve(items: Iterable[T]) -> list[T]:
    """Deduplicate while preserving order."""
    seen: set[T] = set()
    result: list[T] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def truncate_lines(lines: Sequence[str], max_lines: int) -> tuple[list[str], bool]:
    """Truncate to a maximum number of lines, returning truncation status."""
    if max_lines <= 0:
        return [], len(lines) > 0
    if len(lines) <= max_lines:
        return list(lines), False
    return list(lines[:max_lines]), True


def safe_truncate(
    text: str, max_chars: int, *, suffix: str = "...[TRUNCATED]"
) -> tuple[str, bool]:
    """Truncate text deterministically to max_chars with a suffix."""
    if max_chars <= 0:
        return "", len(text) > 0
    if len(text) <= max_chars:
        return text, False
    if max_chars <= len(suffix):
        return suffix[:max_chars], True
    return text[: max_chars - len(suffix)] + suffix, True


def format_section(title: str, body: str) -> str:
    """Format a titled section with a body."""
    if not body:
        return title
    return f"{title}\n{body}"


def format_notes(notes: Sequence[str]) -> str:
    """Format notes as a deterministic bullet list."""
    cleaned = [note.strip() for note in notes if note.strip()]
    deduped = dedupe_preserve(cleaned)
    if not deduped:
        return ""
    body = "\n".join(f"- {note}" for note in deduped)
    return format_section("NOTES", body)
