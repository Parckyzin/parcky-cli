from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from rich.table import Table
from rich.text import Text

from .console import console
from .prompts import prompt
from .provider_select import select_provider

_MANUAL_LABEL = "✍ Type manually..."
_CHANGE_PROVIDER_LABEL = "Change provider"

SelectionAction = Literal["model", "change_provider", "cancel"]


@dataclass(frozen=True)
class SelectionResult:
    action: SelectionAction
    value: str | None = None


@dataclass
class _TuiState:
    models: list[str]
    current_model: str
    show_change_provider: bool
    filter_text: str = ""
    selected_index: int = 0

    def filtered_models(self) -> list[str]:
        return _filter_models(self.models, self.filter_text)

    def options(self, filtered: list[str] | None = None) -> list[str]:
        base = filtered if filtered is not None else self.filtered_models()
        options: list[str] = []
        if self.show_change_provider:
            options.append(_CHANGE_PROVIDER_LABEL)
        options.extend(base)
        options.append(_MANUAL_LABEL)
        return options

    def clamp_selection(self, options_len: int) -> None:
        if options_len <= 0:
            self.selected_index = 0
            return
        self.selected_index = max(0, min(self.selected_index, options_len - 1))


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
            console.print(f"[bold green]✅ Model set to:[/bold green] {result.value}")
            return


def _select_with_prompt_toolkit(
    models: list[str],
    current_model: str,
    show_change_provider: bool,
) -> SelectionResult:
    try:
        from prompt_toolkit.application import Application
        from prompt_toolkit.formatted_text import FormattedText
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.styles import Style
    except ImportError as exc:
        raise ImportError("prompt_toolkit not installed") from exc

    state = _TuiState(
        models=models,
        current_model=current_model,
        show_change_provider=show_change_provider,
    )

    def _render() -> FormattedText:
        filtered = state.filtered_models()
        options = state.options(filtered)
        state.clamp_selection(len(options))

        text: list[tuple[str, str]] = []
        text.append(("class:header", "Select AI Model\n"))
        text.append(("class:muted", f"Current: {current_model}\n"))
        text.append(("class:muted", f"Matches: {len(filtered)}\n"))
        if state.filter_text:
            text.append(("class:muted", f"Filter: {state.filter_text}\n"))
        text.append(("", "\n"))

        if not filtered and state.filter_text:
            text.append(
                ("class:warning", "No matches. Press Ctrl+U to clear filter.\n")
            )
            text.append(("", "\n"))

        for idx, model in enumerate(options):
            is_selected = idx == state.selected_index
            prefix = "➤ " if is_selected else "  "

            if model == _MANUAL_LABEL:
                line_style = "class:manual"
            elif model == _CHANGE_PROVIDER_LABEL:
                line_style = "class:provider"
            elif model == current_model:
                line_style = "class:current"
            else:
                line_style = "class:item"

            if is_selected:
                line_style = f"{line_style} class:selected"

            status = "  ● current" if model == current_model else ""
            text.append((line_style, f"{prefix}{model}{status}\n"))

        text.append(("", "\n"))
        text.append(
            (
                "class:muted",
                "↑/↓ move • Enter select • Esc cancel • '/' filter • Ctrl+U clear",
            )
        )
        return FormattedText(text)

    kb = KeyBindings()

    @kb.add("up")
    def _move_up(event) -> None:
        state.selected_index = max(0, state.selected_index - 1)
        event.app.invalidate()

    @kb.add("down")
    def _move_down(event) -> None:
        filtered = state.filtered_models()
        options_len = len(state.options(filtered))
        if options_len <= 0:
            state.selected_index = 0
        else:
            state.selected_index = min(state.selected_index + 1, options_len - 1)
        event.app.invalidate()

    @kb.add("enter")
    def _select(event) -> None:
        filtered = state.filtered_models()
        options = state.options(filtered)
        if not options:
            event.app.exit(result=SelectionResult(action="cancel"))
            return

        state.clamp_selection(len(options))
        selected = options[state.selected_index]

        if selected == _CHANGE_PROVIDER_LABEL:
            event.app.exit(result=SelectionResult(action="change_provider"))
            return

        if selected == _MANUAL_LABEL:
            manual = _prompt_manual_model()
            if manual:
                event.app.exit(result=SelectionResult(action="model", value=manual))
            else:
                event.app.exit(result=SelectionResult(action="cancel"))
            return

        event.app.exit(result=SelectionResult(action="model", value=selected))

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
        if state.filter_text:
            state.filter_text = state.filter_text[:-1]
            state.selected_index = 0
            event.app.invalidate()

    @kb.add("c-u")
    def _clear_filter(event) -> None:
        state.filter_text = ""
        state.selected_index = 0
        event.app.invalidate()

    @kb.add("<any>")
    def _type_to_filter(event) -> None:
        data = event.data
        if not data or not data.isprintable():
            return
        if data in ("\n", "\r", "\x1b", "\t"):
            return
        state.filter_text += data
        state.selected_index = 0
        event.app.invalidate()

    style = Style.from_dict(
        {
            "header": "bold",
            "muted": "ansibrightblack",
            "warning": "ansiyellow",
            "item": "",
            "current": "ansigreen",
            "manual": "ansiyellow",
            "provider": "ansicyan",
            "selected": "reverse",
        }
    )

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

    table = Table(show_header=True, header_style="bold", title="Select AI Model")
    table.add_column("#", style="dim", width=4)
    table.add_column("Model")
    table.add_column("Status", width=12)

    display: list[str] = []
    if show_change_provider:
        display.append(_CHANGE_PROVIDER_LABEL)
    display.extend(models[:20])
    display.append(_MANUAL_LABEL)

    for idx, model in enumerate(display, start=1):
        if model == _CHANGE_PROVIDER_LABEL:
            table.add_row(str(idx), Text(model, style="cyan"), "")
            continue
        if model == _MANUAL_LABEL:
            table.add_row(str(idx), Text(model, style="yellow"), "")
            continue
        status = "● current" if model == current_model else ""
        style = "green" if model == current_model else "cyan"
        table.add_row(str(idx), Text(model, style=style), status)

    console.print(table)
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
        if 1 <= choice <= len(display):
            selected = display[choice - 1]
            if selected == _CHANGE_PROVIDER_LABEL:
                return SelectionResult(action="change_provider")
            if selected == _MANUAL_LABEL:
                manual = _prompt_manual_model()
                if manual:
                    return SelectionResult(action="model", value=manual)
                return SelectionResult(action="cancel")
            return SelectionResult(action="model", value=selected)
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
