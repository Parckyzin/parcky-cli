from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from prompt_toolkit.formatted_text import FormattedText

from ai_cli.cli.ui.components.select.keys import SelectResult, handle_key
from ai_cli.cli.ui.components.select.state import SelectOption, SelectState
from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme
from ai_cli.cli.ui.drivers.prompt_toolkit import select_with_prompt_toolkit
from ai_cli.cli.ui.renderers.frame import SELECT_FOOTER
from ai_cli.cli.ui.renderers.shell import render_shell
from ai_cli.cli.ui.renderers.text_table import render_text_table

T = TypeVar("T")


def select(
    options: Iterable[SelectOption[T]],
    *,
    title: str | None = None,
    theme: Theme = DEFAULT_THEME,
    key_source: Iterable[str] | None = None,
) -> T | None:
    state = SelectState.from_options(list(options))
    if key_source is not None:
        for key in key_source:
            result: SelectResult[T] = handle_key(state, key)
            if result.action == "select":
                return result.value
            if result.action == "cancel":
                return None
        return None

    return select_with_prompt_toolkit(
        state,
        render=lambda s: _render_select_shell(s, title=title, theme=theme),
    )


def _render_select_shell(
    state: SelectState[T],
    *,
    title: str | None,
    theme: Theme,
) -> FormattedText:
    headers = ["", "Option", "Description", "Status"]
    rows: list[list[tuple[str, str]]] = []
    for idx, option in enumerate(state.options):
        row_style, cell_style, status_style = _row_styles(option, state, idx)
        status_text = (
            f"{theme.current_marker} {theme.current_label}" if option.is_current else ""
        )
        rows.append(
            [
                (
                    row_style["marker"],
                    theme.selected_marker if state.index == idx else " ",
                ),
                (cell_style, option.label),
                (cell_style, option.description or ""),
                (status_style, status_text),
            ]
        )
    body = render_text_table(headers=headers, rows=rows)
    return render_shell(
        title=title or "Select",
        context=None,
        body=body,
        footer=SELECT_FOOTER,
        theme=theme,
    )


def _row_styles(
    option: SelectOption[T],
    state: SelectState[T],
    idx: int,
) -> tuple[dict[str, str], str, str]:
    is_selected = state.index == idx
    if option.disabled:
        return (
            {"marker": "class:marker"},
            "class:disabled",
            "class:disabled",
        )
    if is_selected:
        base = "class:selected_row"
        status = "class:selected_row"
        if option.is_current:
            status = "class:selected_row class:current"
        return (
            {"marker": "class:marker"},
            base,
            status,
        )
    if option.is_current:
        return (
            {"marker": "class:marker"},
            "class:current",
            "class:current",
        )
    return (
        {"marker": "class:marker"},
        "class:accent",
        "class:muted",
    )
