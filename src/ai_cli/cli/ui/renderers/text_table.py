from __future__ import annotations

from collections.abc import Iterable, Sequence

from prompt_toolkit.formatted_text import FormattedText

def render_text_table(
    *,
    headers: Sequence[str],
    rows: Sequence[Sequence[tuple[str, str]]],
    header_class: str = "class:header",
) -> FormattedText:
    widths = _compute_widths(headers, rows)
    parts: list[tuple[str, str]] = []

    if headers:
        parts.extend(_render_row(headers, widths, header_class))
        parts.append(("", "\n"))

    for row in rows:
        parts.extend(_render_row_cells(row, widths))
        parts.append(("", "\n"))

    return FormattedText(parts)


def _compute_widths(
    headers: Sequence[str],
    rows: Sequence[Sequence[tuple[str, str]]],
) -> list[int]:
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, (style, text) in enumerate(row):
            if idx >= len(widths):
                widths.append(len(text))
            else:
                widths[idx] = max(widths[idx], len(text))
    return widths


def _render_row(
    cells: Sequence[str],
    widths: Sequence[int],
    style: str,
) -> Iterable[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    for idx, cell in enumerate(cells):
        padding = widths[idx] - len(cell)
        parts.append((style, cell))
        parts.append(("", " " * (padding + 2)))
    return parts


def _render_row_cells(
    cells: Sequence[tuple[str, str]],
    widths: Sequence[int],
) -> Iterable[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    for idx, (style, text) in enumerate(cells):
        padding = widths[idx] - len(text)
        parts.append((style, text))
        parts.append(("", " " * (padding + 2)))
    return parts
