from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console, Group
from rich.text import Text

from ai_cli.core.common.enums import AvailableProviders

from ai_cli.cli.ui.components.select import SelectOption, SelectState, handle_key
from ai_cli.cli.ui.renderers.select_table import TableColumnSpec, render_table
from ai_cli.cli.ui.console import console
from ai_cli.cli.ui.prompts import prompt

_MANUAL_LABEL = "Type manually..."
_MANUAL_VALUE = "__manual__"


@dataclass(frozen=True)
class ProviderOption:
    key: str
    label: str
    description: str


def select_provider(
    current: str | None = None,
    *,
    providers: list[AvailableProviders] | None = None,
    title: str | None = None,
    allow_manual: bool = True,
) -> str | None:
    """Select an AI provider using the shared Select component."""
    options = _get_provider_options(providers)
    if not options:
        return None

    current_key = current.lower() if current else None
    select_options: list[SelectOption[str]] = [
        SelectOption(
            value=option.key,
            label=option.label,
            description=option.description,
            is_current=option.key == current_key,
        )
        for option in options
    ]
    if allow_manual:
        select_options.append(
            SelectOption(
                value=_MANUAL_VALUE,
                label=_MANUAL_LABEL,
                description=None,
            )
        )

    try:
        selection = _select_with_prompt_toolkit(
            options, current_key, title or "Select AI Provider", allow_manual
        )
    except ImportError:
        console.print(
            "[yellow]prompt_toolkit not available. Using text fallback.[/yellow]"
        )
        selection = _select_fallback_text(select_options, title or "Select AI Provider")
    except Exception as exc:
        console.print(
            f"[yellow]Interactive UI failed ({exc}). Using text fallback.[/yellow]"
        )
        selection = _select_fallback_text(select_options, title or "Select AI Provider")

    if selection is None:
        return None
    if selection == _MANUAL_VALUE:
        return _prompt_manual_provider()
    return str(selection).lower()


def _select_with_prompt_toolkit(
    options: list[ProviderOption],
    current: str | None,
    title: str,
    allow_manual: bool,
) -> str | None:
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

    filter_text = ""
    visible = _filter_options(options, filter_text)
    state = SelectState.from_options(
        _build_select_options(visible, current, allow_manual)
    )

    def _reset_options(new_visible: list[ProviderOption]) -> None:
        state.options = _build_select_options(new_visible, current, allow_manual)
        state.index = _first_enabled_index(state.options)

    def _render() -> ANSI:
        group = Group(
            f"[bold]{title}[/bold]",
            f"[dim]Current: {current}[/dim]" if current else "",
            f"[dim]Filter: {filter_text}[/dim]" if filter_text else "",
            render_table(state, show_index=False, columns=_provider_columns()),
            "[dim]Up/Down move • Enter select • Esc cancel • type to filter[/dim]",
        )
        temp_console = Console(width=console.width, color_system=console.color_system)
        temp_console.begin_capture()
        temp_console.print(group)
        content = temp_console.end_capture()
        return ANSI(content)

    kb = KeyBindings()

    @kb.add("up")
    def _move_up(event) -> None:
        handle_key(state, "up")
        event.app.invalidate()

    @kb.add("down")
    def _move_down(event) -> None:
        handle_key(state, "down")
        event.app.invalidate()

    @kb.add("enter")
    def _select(event) -> None:
        result = handle_key(state, "enter")
        if result.action != "select":
            return
        selection = result.value
        if selection is None:
            event.app.exit(result=None)
            return
        if selection == _MANUAL_VALUE:
            event.app.exit(result=_prompt_manual_provider())
            return
        event.app.exit(result=str(selection))

    @kb.add("escape")
    @kb.add("c-c")
    def _cancel(event) -> None:
        event.app.exit(result=None)

    @kb.add("backspace")
    @kb.add("c-h")
    def _backspace(event) -> None:
        nonlocal filter_text, visible
        if filter_text:
            filter_text = filter_text[:-1]
            visible = _filter_options(options, filter_text)
            _reset_options(visible)
            event.app.invalidate()

    @kb.add("c-l")
    def _clear(event) -> None:
        nonlocal filter_text, visible
        filter_text = ""
        visible = _filter_options(options, filter_text)
        _reset_options(visible)
        event.app.invalidate()

    @kb.add("<any>")
    def _filter(event) -> None:
        nonlocal filter_text, visible
        data = event.data
        if not data or not data.isprintable():
            return
        if data in ("\n", "\r", "\x1b"):
            return
        filter_text += data
        visible = _filter_options(options, filter_text)
        _reset_options(visible)
        event.app.invalidate()

    style = Style.from_dict({"header": "bold", "muted": "ansibrightblack"})
    app = Application(
        layout=Layout(Window(FormattedTextControl(_render), wrap_lines=False)),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )
    return app.run()


def _select_fallback_text(
    options: list[SelectOption[str]],
    title: str,
) -> str | None:
    state = SelectState.from_options(options)
    console.print(
        render_table(state, title=title, show_index=True, columns=_provider_columns())
    )
    user_input = prompt("Enter number, provider name, or blank to cancel").strip()
    if not user_input or user_input.lower() in {"q", "quit"}:
        return None
    if user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(state.options):
            selected = state.options[choice - 1].value
            if selected == _MANUAL_VALUE:
                return _prompt_manual_provider()
            return str(selected)
        return None
    return user_input.lower()


def _prompt_manual_provider() -> str | None:
    manual = prompt("Enter provider name (blank to cancel)").strip()
    if not manual:
        return None
    return manual.lower()


def _build_select_options(
    options: list[ProviderOption],
    current: str | None,
    allow_manual: bool,
) -> list[SelectOption[str]]:
    select_options: list[SelectOption[str]] = [
        SelectOption(
            value=option.key,
            label=option.label,
            description=option.description,
            is_current=option.key == current,
        )
        for option in options
    ]
    if allow_manual:
        select_options.append(
            SelectOption(
                value=_MANUAL_VALUE,
                label=_MANUAL_LABEL,
                description=None,
            )
        )
    return select_options


def _first_enabled_index(options: list[SelectOption[str]]) -> int | None:
    for idx, option in enumerate(options):
        if not option.disabled:
            return idx
    return None


def _provider_columns() -> list[TableColumnSpec[str]]:
    return [
        TableColumnSpec(
            header="",
            width=2,
            render=lambda _opt, _state, _idx, styles, _theme: Text(
                styles.marker, style=styles.marker_style
            ),
        ),
        TableColumnSpec(
            header="Provider",
            render=lambda opt, _state, _idx, styles, _theme: Text(
                opt.label, style=styles.label_style
            ),
        ),
        TableColumnSpec(
            header="Description",
            render=lambda opt, _state, _idx, styles, _theme: Text(
                opt.description or "", style=styles.row_style
            ),
        ),
        TableColumnSpec(
            header="Status",
            width=12,
            render=lambda opt, _state, _idx, styles, theme: Text(
                f"{theme.current_marker} {theme.current_label}"
                if opt.is_current
                else "",
                style=styles.status_style,
            ),
        ),
    ]


def _filter_options(
    options: list[ProviderOption], filter_text: str
) -> list[ProviderOption]:
    if not filter_text:
        return list(options)
    needle = filter_text.casefold()
    return [
        option
        for option in options
        if needle in option.label.casefold() or needle in option.description.casefold()
    ]


def _get_provider_options(
    providers: list[AvailableProviders] | None = None,
) -> list[ProviderOption]:
    descriptions = {
        AvailableProviders.OPENAI: ("OpenAI", "OpenAI GPT models"),
        AvailableProviders.ANTHROPIC: ("Anthropic", "Claude models"),
        AvailableProviders.GOOGLE: ("Gemini", "Google Gemini models"),
        AvailableProviders.LOCAL: ("Local", "Local or self-hosted models"),
    }
    selected = providers or list(AvailableProviders)
    return [
        ProviderOption(
            key=provider.value,
            label=descriptions[provider][0],
            description=descriptions[provider][1],
        )
        for provider in selected
    ]
