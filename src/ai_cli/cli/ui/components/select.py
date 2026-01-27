from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Callable, Generic, Literal, TypeVar

from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from ..console import console
from .theme import DEFAULT_THEME, Theme

T = TypeVar("T")

KeyAction = Literal["select", "cancel", "none"]


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
    justify: str | None = None
    style: str | None = None
    render: Callable[
        [SelectOption[T], SelectState[T], int, RowStyles, Theme], RenderableType
    ] = lambda _opt, _state, _idx, _styles, _theme: ""


@dataclass(frozen=True)
class SelectOption(Generic[T]):
    value: T
    label: str
    description: str | None = None
    disabled: bool = False
    is_current: bool = False


@dataclass
class SelectState(Generic[T]):
    options: list[SelectOption[T]]
    index: int | None

    @classmethod
    def from_options(cls, options: Sequence[SelectOption[T]]) -> SelectState[T]:
        option_list = list(options)
        index = _first_enabled_index(option_list)
        return cls(options=option_list, index=index)

    def current(self) -> SelectOption[T] | None:
        if self.index is None:
            return None
        if 0 <= self.index < len(self.options):
            return self.options[self.index]
        return None

    def move_up(self) -> None:
        self._move(-1)

    def move_down(self) -> None:
        self._move(1)

    def confirm(self) -> T | None:
        option = self.current()
        if option is None or option.disabled:
            return None
        return option.value

    def _move(self, direction: int) -> None:
        if self.index is None or not self.options:
            return
        next_index = _next_enabled_index(self.options, self.index, direction)
        self.index = next_index


@dataclass(frozen=True)
class SelectResult(Generic[T]):
    action: KeyAction
    value: T | None = None


def handle_key(state: SelectState[T], key: str) -> SelectResult[T]:
    key_lower = key.lower()
    if key_lower in {"up", "k"}:
        state.move_up()
        return SelectResult(action="none")
    if key_lower in {"down", "j"}:
        state.move_down()
        return SelectResult(action="none")
    if key_lower in {"enter", "return"}:
        return SelectResult(action="select", value=state.confirm())
    if key_lower in {"esc", "escape", "q"}:
        return SelectResult(action="cancel")
    return SelectResult(action="none")


def render_table(
    state: SelectState[T],
    *,
    title: str | None = None,
    theme: Theme = DEFAULT_THEME,
    show_index: bool = False,
    columns: list[TableColumnSpec[T]] | None = None,
) -> Table:
    table = Table(show_header=True, header_style=theme.header_style, title=title)
    if show_index:
        table.add_column("#", style=theme.muted_style, width=4)

    specs = columns or _default_columns()
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


def select(
    options: Sequence[SelectOption[T]],
    *,
    title: str | None = None,
    theme: Theme = DEFAULT_THEME,
    key_source: Iterable[str] | None = None,
) -> T | None:
    state = SelectState.from_options(options)
    if key_source is not None:
        for key in key_source:
            result = handle_key(state, key)
            if result.action == "select":
                return result.value
            if result.action == "cancel":
                return None
        return None
    return _select_with_prompt_toolkit(state, title=title, theme=theme)


def _select_with_prompt_toolkit(
    state: SelectState[T],
    *,
    title: str | None = None,
    theme: Theme = DEFAULT_THEME,
) -> T | None:
    try:
        from prompt_toolkit.application import Application
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.styles import Style
    except ImportError as exc:
        raise ImportError("prompt_toolkit not installed") from exc

    def _render() -> ANSI:
        table = render_table(state, title=title, theme=theme)
        console.begin_capture()
        console.print(table)
        content = console.end_capture()
        return ANSI(content)

    kb = KeyBindings()

    @kb.add("up")
    def _move_up(event) -> None:
        state.move_up()
        event.app.invalidate()

    @kb.add("down")
    def _move_down(event) -> None:
        state.move_down()
        event.app.invalidate()

    @kb.add("enter")
    def _confirm(event) -> None:
        event.app.exit(result=state.confirm())

    @kb.add("escape")
    @kb.add("c-c")
    @kb.add("q")
    def _cancel(event) -> None:
        event.app.exit(result=None)

    style = Style.from_dict(
        {
            "header": theme.header_style,
            "muted": theme.muted_style,
        }
    )

    app = Application(
        layout=Layout(Window(FormattedTextControl(_render), wrap_lines=False)),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )
    return app.run()


def _first_enabled_index(options: Sequence[SelectOption[T]]) -> int | None:
    for idx, option in enumerate(options):
        if not option.disabled:
            return idx
    return None


def _next_enabled_index(
    options: Sequence[SelectOption[T]],
    current: int,
    direction: int,
) -> int:
    if direction == 0:
        return current
    step = 1 if direction > 0 else -1
    candidate = current + step
    while 0 <= candidate < len(options):
        if not options[candidate].disabled:
            return candidate
        candidate += step
    return current


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
                _strip_ansi(opt.label), style=styles.label_style
            ),
        ),
        TableColumnSpec(
            header="Description",
            render=lambda opt, _state, _idx, styles, _theme: Text(
                _strip_ansi(opt.description or ""), style=styles.row_style
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


def _strip_ansi(value: str) -> str:
    cleaned = value.replace("\x1b", "")
    while True:
        start = cleaned.find("[")
        end = cleaned.find("m", start)
        if start == -1 or end == -1:
            break
        cleaned = cleaned[:start] + cleaned[end + 1 :]
    return cleaned
