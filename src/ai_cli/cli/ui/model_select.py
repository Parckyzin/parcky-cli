from __future__ import annotations

from typing import TYPE_CHECKING
from rich.table import Table
from rich.text import Text

from ai_cli.config.writer import read_env_value, set_env_value

from .console import console
from .prompts import confirm, prompt

if TYPE_CHECKING:
    from pathlib import Path
    from ai_cli.config.cache import Cache


def interactive_model_select(active_path: "Path", cache: "Cache") -> None:
    """Interactive model selection with arrow keys navigation."""
    models = cache.get_model_history()
    current_model = (
        read_env_value(active_path, "AI_MODEL")
        or read_env_value(active_path, "MODEL_NAME")
        or "gemini-2.0-flash"
    )
    selected_idx = 0

    for i, model in enumerate(models):
        if model == current_model:
            selected_idx = i
            break

    while True:
        console.print(_render_table(models, selected_idx, current_model))
        console.print(
            "\n[bold] Highly recommended to use 'weak' models for faster responses. [/bold]"
        )
        console.print(
            "\n[dim]↑/↓: Navigate | Enter: Select | n: New | d: Delete | q: Quit[/dim]"
        )

        key = _get_keypress()

        if key in ("q", "Q", "\x1b"):  # q or Escape
            console.print("[yellow]Cancelled.[/yellow]")
            return

        if key in ("\r", "\n") and models:  # Enter
            selected = models[selected_idx]
            cache.add_model_to_history(selected)
            set_env_value(active_path, "AI_MODEL", selected)
            console.print(f"\n[bold green]✅ Model set to:[/bold green] {selected}")
            return

        if key in ("k", "K", "\x1b[A"):  # Up arrow or k
            selected_idx = (selected_idx - 1) % len(models) if models else 0

        if key in ("j", "J", "\x1b[B"):  # Down arrow or j
            selected_idx = (selected_idx + 1) % len(models) if models else 0

        if key in ("n", "N"):  # New model
            console.print("\n[bold]Add New Model[/bold]")
            new_model = prompt("Enter model name (empty to cancel)", default="")
            if new_model.strip():
                cache.add_model_to_history(new_model.strip())
                set_env_value(active_path, "AI_MODEL", new_model.strip())
                console.print(
                    f"\n[bold green]✅ Model set to:[/bold green] {new_model.strip()}"
                )
                return
            models = cache.get_model_history()

        if key in ("d", "D"):  # Delete
            if models and len(models) > 1:
                model_to_delete = models[selected_idx]
                console.print(
                    f"\n[bold yellow]Delete model:[/bold yellow] {model_to_delete}"
                )
                if confirm("Are you sure?", default=False):
                    cache.remove_model_from_history(model_to_delete)
                    models = cache.get_model_history()
                    selected_idx = min(selected_idx, len(models) - 1)
                    console.print(f"[yellow]Removed:[/yellow] {model_to_delete}")
            elif models:
                console.print("\n[red]Cannot delete the last model.[/red]")
                prompt("Press Enter to continue", default="")


def _render_table(models_list: list[str], sel_idx: int, curr_model: str) -> Table:
    """Render the model selection table."""
    table = Table(show_header=True, header_style="bold", title="🤖 Select AI Model")
    table.add_column("#", style="dim", width=3)
    table.add_column("Model")
    table.add_column("Status", width=12)

    for i, model in enumerate(models_list):
        prefix = "→ " if i == sel_idx else "  "
        if i == sel_idx:
            model_text = Text(model, style="bold reverse cyan")
        else:
            model_text = Text(model, style="cyan")
        status = "[green]● current[/green]" if model == curr_model else ""
        table.add_row(f"{prefix}{i + 1}", model_text, status)

    return table


def _get_keypress() -> str:
    """Get a single keypress from the user."""
    import sys
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return f"\x1b[{ch3}"
            return ch
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
