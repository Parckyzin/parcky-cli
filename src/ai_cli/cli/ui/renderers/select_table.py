from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable, Generic, Literal, TypeVar

from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from ai_cli.cli.ui.components.select.state import SelectOption, SelectState
from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme

T = TypeVar("T")


@dataclass(frozen=True)
class RowStyles:
    marker: str
    marker_style: str
    label_style: str
    row_style: str
    status_style: str


@dataclass(frozen=True)
class TableColumnSpec(Generic[T]):
    header: str
    width: int | None = None
    justify: Literal["left", "center", "right"] | None = None
    style: str | None = None
    render: Callable[
        [SelectOption[T], SelectState[T], int, RowStyles, Theme], RenderableType
    ] = lambda _opt, _state, _idx, _styles, _theme: ""


def render_table(
    state: SelectState[T],
    *,
    title: str | None = None,
    theme: Theme = DEFAULT_THEME,
    show_index: bool = False,
    columns: Sequence[TableColumnSpec[T]] | None = None,
) -> Table:
    table = Table(show_header=True, header_style=theme.header_style, title=title)
    if show_index:
        table.add_column("#", style=theme.muted_style, width=4)

    specs = list(columns) if columns is not None else _default_columns()
    for spec in specs:
        table.add_column(
            spec.header,
            width=spec.width,
            justify=spec.justify,
            style=spec.style,
        )

    if not state.options:
        empty_row = [
            Text(theme.empty_label, style=theme.muted_style) if idx == 0 else ""
            for idx in range(len(specs))
        ]
        if show_index:
            empty_row.insert(0, "")
        table.add_row(*empty_row)
        return table

    for idx, option in enumerate(state.options):
        styles = _compute_row_styles(option, state, idx, theme)
        row = [spec.render(option, state, idx, styles, theme) for spec in specs]
        if show_index:
            row.insert(0, str(idx + 1))
        table.add_row(*row)
    return table


def _compute_row_styles(
    option: SelectOption[T],
    state: SelectState[T],
    idx: int,
    theme: Theme,
) -> RowStyles:
    is_selected = state.index == idx
    if option.disabled:
        return RowStyles(
            marker=theme.disabled_marker,
            marker_style=theme.marker_style,
            label_style=theme.disabled_style,
            row_style=theme.disabled_style,
            status_style=theme.disabled_style,
        )
    if is_selected:
        return RowStyles(
            marker=theme.selected_marker,
            marker_style=theme.marker_style,
            label_style=theme.selected_style,
            row_style=theme.selected_row_style,
            status_style=theme.selected_row_style,
        )
    if option.is_current:
        return RowStyles(
            marker=" ",
            marker_style=theme.marker_style,
            label_style=theme.current_style,
            row_style=theme.current_style,
            status_style=theme.current_style,
        )
    return RowStyles(
        marker=" ",
        marker_style=theme.marker_style,
        label_style=theme.accent_style,
        row_style=theme.muted_style,
        status_style=theme.muted_style,
    )


def _default_columns() -> list[TableColumnSpec[T]]:
    return [
        TableColumnSpec(
            header="",
            width=2,
            render=lambda _opt, _state, _idx, styles, _theme: Text(
                styles.marker, style=styles.marker_style
            ),
        ),
        TableColumnSpec(
            header="Option",
            render=lambda opt, _state, _idx, styles, _theme: Text(
                strip_ansi(opt.label), style=styles.label_style
            ),
        ),
        TableColumnSpec(
            header="Description",
            render=lambda opt, _state, _idx, styles, _theme: Text(
                strip_ansi(opt.description or ""), style=styles.row_style
            ),
        ),
        TableColumnSpec(
            header="Status",
            width=10,
            render=lambda opt, _state, _idx, styles, theme: Text(
                f"{theme.current_marker} {theme.current_label}"
                if opt.is_current
                else "",
                style=styles.status_style,
            ),
        ),
    ]


def strip_ansi(value: str) -> str:
    cleaned = value.replace("\x1b", "")
    while True:
        start = cleaned.find("[")
        end = cleaned.find("m", start)
        if start == -1 or end == -1:
            break
        cleaned = cleaned[:start] + cleaned[end + 1 :]
    return cleaned
