from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from ai_cli.cli.ui.components.select.keys import SelectResult, handle_key
from ai_cli.cli.ui.components.select.state import SelectOption, SelectState
from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme
from ai_cli.cli.ui.drivers.prompt_toolkit import select_with_prompt_toolkit
from ai_cli.cli.ui.renderers.select_table import render_table

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
        render=lambda s: render_table(s, title=title, theme=theme),
    )
