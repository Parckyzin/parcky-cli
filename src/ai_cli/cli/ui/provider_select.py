from __future__ import annotations

from dataclasses import dataclass

from rich.table import Table
from rich.text import Text

from ai_cli.core.common.enums import AvailableProviders

from .console import console
from .prompts import prompt

_MANUAL_LABEL = "Type manually..."


@dataclass(frozen=True)
class ProviderOption:
    key: str
    label: str
    description: str


@dataclass
class _TuiState:
    options: list[ProviderOption]
    current: str | None
    filter_text: str = ""
    selected_index: int = 0

    def visible_options(self) -> list[ProviderOption]:
        return _filter_options(self.options, self.filter_text)

    def labels(self) -> list[str]:
        return [opt.label for opt in self.visible_options()] + [_MANUAL_LABEL]

    def clamp_selection(self) -> None:
        labels = self.labels()
        if not labels:
            self.selected_index = 0
            return
        self.selected_index = max(0, min(self.selected_index, len(labels) - 1))


def select_provider(current: str | None = None) -> str | None:
    """Select an AI provider with a prompt-toolkit UI and fallback."""
    options = _get_provider_options()
    if not options:
        return None

    if current:
        current = current.lower()

    try:
        return _select_with_prompt_toolkit(options, current)
    except ImportError:
        console.print("[yellow]prompt_toolkit not available. Using text fallback.[/yellow]")
    except Exception as exc:
        console.print(
            f"[yellow]Interactive UI failed ({exc}). Using text fallback.[/yellow]"
        )

    return _select_fallback_text(options, current)


def _select_with_prompt_toolkit(
    options: list[ProviderOption],
    current: str | None,
) -> str | None:
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

    state = _TuiState(options=options, current=current)

    def _render() -> FormattedText:
        state.clamp_selection()
        visible = state.visible_options()
        labels = state.labels()
        text: list[tuple[str, str]] = []
        text.append(("class:header", "Select AI Provider\n"))
        if current:
            text.append(("class:muted", f"Current: {current}\n"))
        if state.filter_text:
            text.append(("class:muted", f"Filter: {state.filter_text}\n"))
        text.append(("", "\n"))

        for idx, label in enumerate(labels):
            is_selected = idx == state.selected_index
            prefix = "-> " if is_selected else "   "
            style = "class:selected" if is_selected else ""
            if label == _MANUAL_LABEL:
                text.append((style, f"{prefix}{label}\n"))
                continue

            option = visible[idx]
            suffix = " (current)" if option.key == current else ""
            row = f"{prefix}{option.label}{suffix}\n"
            text.append((style, row))
            text.append(("class:muted", f"     {option.description}\n"))

        text.append(("", "\n"))
        text.append(
            ("class:muted", "Up/Down move • Enter select • Esc cancel • type to filter")
        )
        return FormattedText(text)

    kb = KeyBindings()

    @kb.add("up")
    def _move_up(event) -> None:
        state.selected_index = max(0, state.selected_index - 1)
        event.app.invalidate()

    @kb.add("down")
    def _move_down(event) -> None:
        state.selected_index += 1
        event.app.invalidate()

    @kb.add("enter")
    def _select(event) -> None:
        labels = state.labels()
        if not labels:
            event.app.exit(result=None)
            return
        selected = labels[state.selected_index]
        if selected == _MANUAL_LABEL:
            event.app.exit(result=_prompt_manual_provider())
            return
        visible = state.visible_options()
        if state.selected_index < len(visible):
            event.app.exit(result=visible[state.selected_index].key)
            return
        event.app.exit(result=None)

    @kb.add("escape")
    @kb.add("c-c")
    def _cancel(event) -> None:
        event.app.exit(result=None)

    @kb.add("backspace")
    @kb.add("c-h")
    def _backspace(event) -> None:
        if state.filter_text:
            state.filter_text = state.filter_text[:-1]
            state.selected_index = 0
            event.app.invalidate()

    @kb.add("c-l")
    def _clear(event) -> None:
        state.filter_text = ""
        state.selected_index = 0
        event.app.invalidate()

    @kb.add("<any>")
    def _filter(event) -> None:
        data = event.data
        if not data or not data.isprintable():
            return
        if data in ("\n", "\r", "\x1b"):
            return
        state.filter_text += data
        state.selected_index = 0
        event.app.invalidate()

    style = Style.from_dict(
        {
            "header": "bold",
            "muted": "ansibrightblack",
            "selected": "reverse",
        }
    )

    app = Application(
        layout=Layout(Window(FormattedTextControl(_render), wrap_lines=False)),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )
    return app.run()


def _select_fallback_text(
    options: list[ProviderOption],
    current: str | None,
) -> str | None:
    table = Table(show_header=True, header_style="bold", title="Select AI Provider")
    table.add_column("#", style="dim", width=4)
    table.add_column("Provider")
    table.add_column("Description")
    table.add_column("Status", width=12)

    for idx, option in enumerate(options, start=1):
        status = "(current)" if option.key == current else ""
        table.add_row(
            str(idx),
            Text(option.label, style="cyan"),
            option.description,
            status,
        )

    console.print(table)
    user_input = prompt(
        "Enter number, provider name, or blank to cancel"
    ).strip()
    if not user_input or user_input.lower() in {"q", "quit"}:
        return None
    if user_input.isdigit():
        choice = int(user_input)
        if 1 <= choice <= len(options):
            return options[choice - 1].key
    return user_input.lower()


def _prompt_manual_provider() -> str | None:
    manual = prompt("Enter provider name (blank to cancel)").strip()
    if not manual:
        return None
    return manual.lower()


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


def _get_provider_options() -> list[ProviderOption]:
    descriptions = {
        AvailableProviders.OPENAI: ("OpenAI", "OpenAI GPT models"),
        AvailableProviders.ANTHROPIC: ("Anthropic", "Claude models"),
        AvailableProviders.GOOGLE: ("Gemini", "Google Gemini models"),
        AvailableProviders.LOCAL: ("Local", "Local or self-hosted models"),
    }
    return [
        ProviderOption(
            key=provider,
            label=descriptions[provider][0],
            description=descriptions[provider][1],
        )
        for provider in AvailableProviders
    ]
