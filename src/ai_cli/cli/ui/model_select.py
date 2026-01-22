from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rich.table import Table
from rich.text import Text

from .console import console
from .prompts import prompt

_MANUAL_LABEL = "✍ Type manually..."


@dataclass
class _TuiState:
    models: list[str]
    current_model: str
    filter_text: str = ""
    selected_index: int = 0
    filter_mode: bool = False  # when True, typed chars go only to filter

    def filtered_models(self) -> list[str]:
        return _filter_models(self.models, self.filter_text)

    def options(self, filtered: list[str] | None = None) -> list[str]:
        base = filtered if filtered is not None else self.filtered_models()
        return base + [_MANUAL_LABEL]

    def clamp_selection(self, options_len: int) -> None:
        if options_len <= 0:
            self.selected_index = 0
            return
        self.selected_index = max(0, min(self.selected_index, options_len - 1))


def interactive_model_select(
        models: list[str],
        current_model: str,
        on_select: Callable[[str], None],
) -> None:
    """Interactive model selection with a prompt-toolkit UI and fallback.

    - Uses prompt_toolkit when available (cross-platform arrow navigation + filter).
    - Falls back to a simple text prompt if prompt_toolkit is unavailable or fails.
    """
    if not models:
        selected = _select_fallback_text(models, current_model)
        if selected:
            on_select(selected)
            console.print(f"[bold green]✅ Model set to:[/bold green] {selected}")
        else:
            console.print("[yellow]Cancelled.[/yellow]")
        return

    try:
        selected = _select_with_prompt_toolkit(models, current_model)
    except ImportError:
        console.print(
            "[yellow]prompt_toolkit not available. Using text fallback.[/yellow]"
        )
        selected = _select_fallback_text(models, current_model)
    except Exception as exc:
        console.print(
            f"[yellow]Interactive UI failed ({exc}). Using text fallback.[/yellow]"
        )
        selected = _select_fallback_text(models, current_model)

    if selected:
        on_select(selected)
        console.print(f"[bold green]✅ Model set to:[/bold green] {selected}")
    else:
        console.print("[yellow]Cancelled.[/yellow]")


def _select_with_prompt_toolkit(models: list[str], current_model: str) -> str | None:
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

    state = _TuiState(models=models, current_model=current_model)

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
            text.append(("class:warning", "No matches. Press Ctrl+U to clear filter.\n"))
            text.append(("", "\n"))

        for idx, model in enumerate(options):
            is_selected = idx == state.selected_index
            prefix = "➤ " if is_selected else "  "

            if model == _MANUAL_LABEL:
                line_style = "class:manual"
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
            event.app.exit(result=None)
            return

        state.clamp_selection(len(options))
        selected = options[state.selected_index]

        if selected == _MANUAL_LABEL:
            manual = _prompt_manual_model()
            event.app.exit(result=manual)
            return

        event.app.exit(result=selected)

    @kb.add("escape")
    @kb.add("c-c")
    def _cancel(event) -> None:
        event.app.exit(result=None)

    @kb.add("/")
    def _enter_filter_mode(event) -> None:
        # Nice UX: user presses '/', then types query. Same behavior as typing normally.
        state.filter_mode = True
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
        state.filter_mode = False
        event.app.invalidate()

    @kb.add("<any>")
    def _type_to_filter(event) -> None:
        data = event.data
        if not data or not data.isprintable():
            return
        if data in ("\n", "\r", "\x1b", "\t"):
            return

        # Default behavior: typing filters (common UX for pickers).
        # If you want typing to jump instead of filter later, we can implement jump-to-match.
        state.filter_text += data
        state.selected_index = 0
        state.filter_mode = True
        event.app.invalidate()

    style = Style.from_dict(
        {
            "header": "bold",
            "muted": "ansibrightblack",
            "warning": "ansiyellow",
            "item": "",
            "current": "ansigreen",
            "manual": "ansiyellow",
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
    return app.run()


def _select_fallback_text(models: list[str], current_model: str) -> str | None:
    """Simple, stable fallback when prompt_toolkit isn't available."""
    if not models:
        return _prompt_manual_model()

    table = Table(show_header=True, header_style="bold", title="Select AI Model")
    table.add_column("#", style="dim", width=4)
    table.add_column("Model")
    table.add_column("Status", width=12)

    display = models[:20]
    for idx, model in enumerate(display, start=1):
        status = "● current" if model == current_model else ""
        style = "green" if model == current_model else "cyan"
        table.add_row(str(idx), Text(model, style=style), status)

    console.print(table)
    if len(models) > len(display):
        console.print(f"[dim]Showing first {len(display)} of {len(models)} models.[/dim]")

    user_input = prompt("Enter number | model name | m <name> | blank to cancel").strip()
    if not user_input or user_input.lower() in {"q", "quit"}:
        return None

    if user_input.lower().startswith("m "):
        manual = user_input[2:].strip()
        return manual or None

    if user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(display):
            return display[choice - 1]
        return None

    return user_input


def _prompt_manual_model() -> str | None:
    manual = prompt("Enter model name (blank to cancel)").strip()
    return manual or None


def _filter_models(models: list[str], filter_text: str) -> list[str]:
    if not filter_text:
        return list(models)
    needle = filter_text.casefold()
    return [model for model in models if needle in model.casefold()]
