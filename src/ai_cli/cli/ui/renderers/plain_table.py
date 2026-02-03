from __future__ import annotations

from collections.abc import Sequence


def render_plain_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
) -> str:
    widths = _compute_widths(headers, rows)
    lines: list[str] = []
    if headers:
        lines.append(_render_row(headers, widths))
        lines.append(_render_separator(widths))
    for row in rows:
        lines.append(_render_row(row, widths))
    return "\n".join(lines)


def _compute_widths(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[int]:
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            if idx >= len(widths):
                widths.append(len(cell))
            else:
                widths[idx] = max(widths[idx], len(cell))
    return widths


def _render_row(row: Sequence[str], widths: Sequence[int]) -> str:
    parts: list[str] = []
    for idx, cell in enumerate(row):
        padding = widths[idx] - len(cell)
        parts.append(cell + (" " * padding))
    return "  ".join(parts)


def _render_separator(widths: Sequence[int]) -> str:
    parts = ["-" * width for width in widths]
    return "  ".join(parts)
