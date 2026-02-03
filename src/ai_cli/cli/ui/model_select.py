from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from rich.console import Console, Group, RenderableType
from rich.text import Text

from ai_cli.cli.ui.components.select import SelectOption, SelectState, handle_key
from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme
from ai_cli.cli.ui.console import console
from ai_cli.cli.ui.prompts import prompt
from ai_cli.cli.ui.provider_select import select_provider
from ai_cli.cli.ui.renderers.frame import MODEL_FILTER_FOOTER, render_frame
from ai_cli.cli.ui.renderers.select_table import (
    TableColumnSpec,
    render_table,
    strip_ansi,
)

_MANUAL_LABEL = "✍ Type manually..."
_CHANGE_PROVIDER_LABEL = "Change provider"
_ACTION_MANUAL = object()
_ACTION_CHANGE_PROVIDER = object()

SelectionAction = Literal["model", "change_provider", "cancel"]


@dataclass(frozen=True)
class SelectionResult:
    action: SelectionAction
    value: str | None = None


def interactive_model_select(
    models: list[str],
    current_model: str,
    on_select: Callable[[str], None],
    *,
    current_provider: str | None = None,
    on_change_provider: Callable[[str], tuple[list[str], str | None]] | None = None,
) -> None:
    """Interactive model selection with provider switching support."""
    models_state = models
    model_state = current_model
    provider_state = current_provider
    show_change_provider = on_change_provider is not None

    while True:
        try:
            result = _select_with_prompt_toolkit(
                models_state, model_state, show_change_provider
            )
        except ImportError:
            console.print(
                "[yellow]prompt_toolkit not available. Using text fallback.[/yellow]"
            )
            result = _select_fallback_text(
                models_state, model_state, show_change_provider
            )
        except Exception as exc:
            console.print(
                f"[yellow]Interactive UI failed ({exc}). Using text fallback.[/yellow]"
            )
            result = _select_fallback_text(
                models_state, model_state, show_change_provider
            )

        if result.action == "cancel":
            console.print("[yellow]Cancelled.[/yellow]")
            return

        if result.action == "change_provider":
            if not on_change_provider:
                continue
            selected_provider = select_provider(current=provider_state)
            if not selected_provider:
                continue
            if provider_state and selected_provider == provider_state:
                continue
            models_state, model_state = on_change_provider(selected_provider)
            provider_state = selected_provider
            continue

        if result.action == "model" and result.value:
            on_select(result.value)
            return


def _select_with_prompt_toolkit(
    models: list[str],
    current_model: str,
    show_change_provider: bool,
) -> SelectionResult:
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
    filtered = _filter_models(models, filter_text)
    state = SelectState.from_options(
        _build_options(filtered, current_model, show_change_provider)
    )

    def _reset_options(new_filtered: list[str]) -> None:
        state.options = _build_options(
            new_filtered, current_model, show_change_provider
        )
        state.index = _first_enabled_index(state.options)

    def _render() -> ANSI:
        temp_console = Console(width=console.width, color_system=console.color_system)
        temp_console.begin_capture()
        temp_console.print(
            _render_model_frame(
                title="Select AI Model",
                current_model=current_model,
                filter_text=filter_text,
                matches=len(filtered),
                filtered_empty=not filtered and bool(filter_text),
                state=state,
                theme=DEFAULT_THEME,
                align=True,
            )
        )
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
            event.app.exit(result=SelectionResult(action="cancel"))
            return
        if selection is _ACTION_CHANGE_PROVIDER:
            event.app.exit(result=SelectionResult(action="change_provider"))
            return
        if selection is _ACTION_MANUAL:
            manual = _prompt_manual_model()
            if manual:
                event.app.exit(result=SelectionResult(action="model", value=manual))
            else:
                event.app.exit(result=SelectionResult(action="cancel"))
            return
        event.app.exit(result=SelectionResult(action="model", value=str(selection)))

    @kb.add("escape")
    @kb.add("c-c")
    def _cancel(event) -> None:
        event.app.exit(result=SelectionResult(action="cancel"))

    @kb.add("/")
    def _enter_filter_mode(event) -> None:
        event.app.invalidate()

    @kb.add("backspace")
    @kb.add("c-h")
    def _backspace(event) -> None:
        nonlocal filter_text, filtered
        if filter_text:
            filter_text = filter_text[:-1]
            filtered = _filter_models(models, filter_text)
            _reset_options(filtered)
            event.app.invalidate()

    @kb.add("c-u")
    def _clear_filter(event) -> None:
        nonlocal filter_text, filtered
        filter_text = ""
        filtered = _filter_models(models, filter_text)
        _reset_options(filtered)
        event.app.invalidate()

    @kb.add("<any>")
    def _type_to_filter(event) -> None:
        nonlocal filter_text, filtered
        data = event.data
        if not data or not data.isprintable():
            return
        if data in ("\n", "\r", "\x1b", "\t"):
            return
        filter_text += data
        filtered = _filter_models(models, filter_text)
        _reset_options(filtered)
        event.app.invalidate()

    style = Style.from_dict({"header": "bold", "muted": "ansibrightblack"})
    control = FormattedTextControl(text=_render)
    app = Application(
        layout=Layout(Window(control, wrap_lines=False)),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )
    result = app.run()
    if isinstance(result, SelectionResult):
        return result
    return SelectionResult(action="cancel")


def _select_fallback_text(
    models: list[str],
    current_model: str,
    show_change_provider: bool,
) -> SelectionResult:
    """Simple, stable fallback when prompt_toolkit isn't available."""
    if not models:
        manual = _prompt_manual_model()
        if manual:
            return SelectionResult(action="model", value=manual)
        return SelectionResult(action="cancel")

    display = models[:20]
    state = SelectState.from_options(
        _build_options(display, current_model, show_change_provider)
    )
    console.print(
        _render_model_frame(
            title="Select AI Model",
            current_model=current_model,
            filter_text="",
            matches=len(display),
            filtered_empty=False,
            state=state,
            theme=DEFAULT_THEME,
            show_index=True,
            align=False,
        )
    )
    if len(models) > 20:
        console.print(f"[dim]Showing first 20 of {len(models)} models.[/dim]")

    user_input = prompt(
        "Enter number | model name | m <name> | blank to cancel"
    ).strip()
    if not user_input or user_input.lower() in {"q", "quit"}:
        return SelectionResult(action="cancel")

    if user_input.lower().startswith("m "):
        manual = user_input[2:].strip()
        return SelectionResult(action="model", value=manual or None)

    if user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(state.options):
            selected = state.options[choice - 1].value
            if selected is _ACTION_CHANGE_PROVIDER:
                return SelectionResult(action="change_provider")
            if selected is _ACTION_MANUAL:
                manual = _prompt_manual_model()
                if manual:
                    return SelectionResult(action="model", value=manual)
                return SelectionResult(action="cancel")
            return SelectionResult(action="model", value=str(selected))
        return SelectionResult(action="cancel")

    return SelectionResult(action="model", value=user_input)


def _prompt_manual_model() -> str | None:
    manual = prompt("Enter model name (blank to cancel)").strip()
    return manual or None


def _filter_models(models: list[str], filter_text: str) -> list[str]:
    if not filter_text:
        return list(models)
    needle = filter_text.casefold()
    return [model for model in models if needle in model.casefold()]


def _build_options(
    models: list[str],
    current_model: str,
    show_change_provider: bool,
) -> list[SelectOption[object]]:
    options: list[SelectOption[object]] = []
    if show_change_provider:
        options.append(
            SelectOption(
                value=_ACTION_CHANGE_PROVIDER,
                label=_CHANGE_PROVIDER_LABEL,
                description=None,
            )
        )
    for model in models:
        options.append(
            SelectOption(
                value=model,
                label=model,
                description=None,
                is_current=model == current_model,
            )
        )
    options.append(
        SelectOption(
            value=_ACTION_MANUAL,
            label=_MANUAL_LABEL,
            description=None,
        )
    )
    return options


def _first_enabled_index(options: list[SelectOption[object]]) -> int | None:
    for idx, option in enumerate(options):
        if not option.disabled:
            return idx
    return None


def _model_columns() -> list[TableColumnSpec[object]]:
    return [
        TableColumnSpec(
            header="",
            width=2,
            render=lambda _opt, _state, _idx, styles, _theme: Text(
                styles.marker, style=styles.marker_style
            ),
        ),
        TableColumnSpec(
            header="Model",
            render=lambda opt, _state, _idx, styles, _theme: Text(
                strip_ansi(opt.label), style=styles.label_style
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


def _render_model_frame(
    *,
    title: str,
    current_model: str,
    filter_text: str,
    matches: int,
    filtered_empty: bool,
    state: SelectState[object],
    theme: Theme,
    show_index: bool = False,
    align: bool = False,
) -> RenderableType:
    body: list[RenderableType] = [
        Text(f"Current: {current_model}", style=theme.muted_style),
        Text(f"Matches: {matches}", style=theme.muted_style),
    ]
    if filter_text:
        body.append(Text(f"Filter: {filter_text}", style=theme.muted_style))
    if filtered_empty:
        body.append(
            Text(
                "No matches. Press Ctrl+U to clear filter.",
                style=theme.frame_warn_style,
            )
        )
    body.append(
        render_table(state, show_index=show_index, columns=_model_columns())
    )
    return render_frame(
        title=title,
        body=Group(*body),
        footer=MODEL_FILTER_FOOTER,
        theme=theme,
        align=align,
    )
