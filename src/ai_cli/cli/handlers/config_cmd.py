from __future__ import annotations

import contextlib
import os
from pathlib import Path

import typer
from rich.text import Text

from ai_cli.config.paths import get_global_env_path
from ai_cli.config.settings import ConfigEntry, list_config_entries
from ai_cli.config.writer import (
    read_ai_provider,
    read_env_value,
    set_ai_provider,
    set_env_value,
)
from ai_cli.core.exceptions import AICliError, ExitCode

from ..context import get_context
from ..ui.console import console
from ..ui.components.modal import confirm as modal_confirm
from ..ui.components.select import SelectOption, SelectState, select
from ..ui.drivers.prompt_toolkit import select_with_prompt_toolkit
from ..ui.errors import exit_with_error, exit_with_unexpected_error
from ..ui.panels import config_hint_panel, config_settings_table
from ..ui.prompts import confirm, prompt
from ..ui.provider_select import select_provider as prompt_provider_select
from ..ui.renderers.select_table import TableColumnSpec, render_table, strip_ansi


def register(app: typer.Typer) -> None:
    """Register config-related commands."""

    @app.command()
    def version() -> None:
        """Show version information."""
        console.print("[bold green]AI CLI[/bold green] v0.1.0")
        console.print("🤖 AI-powered git commit and PR creation tool")

    @app.command()
    def setup(
        api_key: str = typer.Option(
            None,
            "--api-key",
            "-k",
            help="Set the AI_API_KEY directly (skips interactive prompt)",
        ),
    ) -> None:
        """
        ⚙️ Configure ai-cli with your API key.

        This command helps you set up ai-cli by configuring your AI_API_KEY
        in the global config (~/.config/ai-cli/.env).

        Examples:
            ai-cli setup                          # Interactive setup
            ai-cli setup --api-key YOUR_KEY       # Set API key directly
        """
        global_path = get_global_env_path()
        global_path.parent.mkdir(parents=True, exist_ok=True)

        def _harden_file_permissions(path: Path) -> None:
            """Best-effort: restrict secrets file to owner read/write."""
            with contextlib.suppress(Exception):
                os.chmod(path, 0o600)

        def get_current_key() -> str:
            if not global_path.exists():
                return ""
            return read_env_value(global_path, "AI_API_KEY") or read_env_value(
                global_path, "GEMINI_API_KEY"
            )

        def save_api_key(key: str) -> None:
            set_env_value(global_path, "AI_API_KEY", key)
            _harden_file_permissions(global_path)

        if api_key:
            save_api_key(api_key)
            console.print(f"[bold green]✅ API key saved to {global_path}[/bold green]")
            return

        console.print("[bold]🤖 AI CLI Setup[/bold]")
        console.print("=" * 40)

        current_key = get_current_key()
        if current_key:
            masked = (
                current_key[:8] + "..." + current_key[-4:]
                if len(current_key) > 12
                else "***"
            )
            console.print(f"\nCurrent API key: [dim]{masked}[/dim]")
            if not confirm("\nUpdate API key?", default=False):
                console.print("[yellow]No changes made.[/yellow]")
                return

        console.print("\n[blue]Get your API key from your provider.[/blue]\n")

        new_key = prompt("Enter your AI_API_KEY")
        if not new_key.strip():
            console.print("[bold red]❌ No API key provided. Aborted.[/bold red]")
            raise typer.Exit(1)

        save_api_key(new_key.strip())
        console.print(f"\n[bold green]✅ API key saved to {global_path}[/bold green]")
        console.print(
            "\n[bold]🎉 Setup complete![/bold] You can now use ai-cli from any project.\n"
        )
        console.print("[dim]Quick start:[/dim]")
        console.print("  ai-cli smart-commit      [dim]# AI-powered commit[/dim]")
        console.print("  ai-cli create-pr         [dim]# Create PR from branch[/dim]")
        console.print("  ai-cli --help            [dim]# See all commands[/dim]")

    @app.command()
    def config(
        edit: bool = typer.Option(
            False,
            "--edit",
            "-e",
            help="Edit editable values (not implemented yet)",
        ),
        set_model: str = typer.Option(
            None, "--model", "-m", help="Set the AI model to use"
        ),
        select_model: bool = typer.Option(
            False, "--select", "-s", help="Interactive model selection"
        ),
        select_provider: bool = typer.Option(
            False, "--provider", "-p", help="Select AI provider"
        ),
        action: str | None = typer.Argument(None, help="Optional action (provider)"),
    ) -> None:
        """
        🔧 Show ai-cli configuration (read-only).

        Examples:
            ai-cli config                    # Show current config
            ai-cli config -e                 # Edit mode (coming soon)
        """
        debug = False
        try:
            ctx = get_context()
            debug = ctx.config.debug
            global_path = get_global_env_path()
            if edit:
                _run_edit_flow(global_path)
                return

            select_provider_flag = select_provider or action == "provider"
            if select_provider_flag:
                current_provider = read_ai_provider(global_path) or ""
                selected = prompt_provider_select(current=current_provider or None)
                if not selected:
                    console.print("[yellow]Cancelled.[/yellow]")
                    return
                set_ai_provider(global_path, selected)
                set_env_value(global_path, "AI_MODEL", "")
                set_env_value(global_path, "MODEL_NAME", "")
                console.print(
                    f"[bold green]✅ Provider set to:[/bold green] {selected}"
                )
                console.print(f"[dim]   Saved to: {global_path}[/dim]")
                return

            if set_model or select_model or action:
                console.print(
                    "[yellow]Config is read-only. Use parcky-cli config -e to edit.[/yellow]"
                )

            _show_config_status(global_path)
        except AICliError as exc:
            exit_with_error(exc, debug=debug)
        except typer.Exit:
            raise
        except Exception as exc:
            exit_with_unexpected_error(exc, debug=debug)


def _show_config_status(global_path: Path) -> None:
    """Show current configuration status."""
    console.print("[bold]🔧 AI CLI Configuration[/bold]\n")

    api_key = read_env_value(global_path, "AI_API_KEY") or read_env_value(
        global_path, "GEMINI_API_KEY"
    )
    model_name = (
        read_env_value(global_path, "AI_MODEL")
        or read_env_value(global_path, "MODEL_NAME")
        or "gemini-2.0-flash"
    )

    console.print("[bold]Current Settings:[/bold]")
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        console.print(f"  API Key: [green]{masked}[/green]")
    else:
        console.print("  API Key: [red]Not set[/red]")

    console.print(f"  Model:   [cyan]{model_name}[/cyan]")
    console.print(f"  Source:  [dim]global ({global_path})[/dim]\n")

    rows = list_config_entries(global_path)
    console.print(config_settings_table(rows))
    console.print(
        config_hint_panel(
            "Tip: To edit editable values, run: parcky-cli config -e"
        )
    )


def _run_edit_flow(global_path: Path) -> None:
    while True:
        category = _select_edit_category()
        if category in {None, "Back", "Exit"}:
            return

        _edit_category(category, global_path)


def _select_edit_category() -> str | None:
    options = [
        SelectOption(value="AI limits", label="AI limits", description="AI limits"),
        SelectOption(value="Git limits", label="Git limits", description="Git limits"),
        SelectOption(value="Back", label="Back", description="Return"),
        SelectOption(value="Exit", label="Exit", description="Exit"),
    ]
    try:
        return select(options, title="Edit configuration")
    except ImportError:
        console.print("[yellow]prompt_toolkit not available. Using text fallback.[/yellow]")
    except Exception as exc:
        console.print(
            f"[yellow]Interactive UI failed ({exc}). Using text fallback.[/yellow]"
        )

    state = SelectState.from_options(options)
    console.print(render_table(state, title="Edit configuration", show_index=True))
    user_input = prompt("Enter number or blank to cancel").strip()
    if not user_input or not user_input.isdigit():
        return None
    choice = int(user_input)
    if 1 <= choice <= len(state.options):
        return str(state.options[choice - 1].value)
    return None


def _edit_category(category: str, global_path: Path) -> None:
    while True:
        entries = [
            entry
            for entry in list_config_entries(global_path)
            if entry.editable and entry.category == category
        ]
        if not entries:
            console.print("[yellow]No editable settings in this category.[/yellow]")
            return

        selection = _select_edit_entry(entries, title=category)
        if selection is None:
            return
        if selection == "Back":
            return
        if isinstance(selection, ConfigEntry):
            _edit_entry(selection, global_path)


def _select_edit_entry(
    entries: list[ConfigEntry],
    *,
    title: str,
) -> ConfigEntry | str | None:
    options: list[SelectOption[ConfigEntry | str]] = [
        SelectOption(
            value=entry,
            label=entry.key,
            description=entry.description,
        )
        for entry in entries
    ]
    options.append(
        SelectOption(value="Back", label="Back", description="Return to categories")
    )
    state = SelectState.from_options(options)

    def _render_table(state_: SelectState[ConfigEntry | str]):
        return render_table(
            state_,
            title=title,
            columns=_edit_columns(),
        )

    try:
        return select_with_prompt_toolkit(state, render=_render_table)
    except ImportError:
        console.print("[yellow]prompt_toolkit not available. Using text fallback.[/yellow]")
    except Exception as exc:
        console.print(
            f"[yellow]Interactive UI failed ({exc}). Using text fallback.[/yellow]"
        )

    console.print(render_table(state, title=title, show_index=True, columns=_edit_columns()))
    user_input = prompt("Enter number or blank to cancel").strip()
    if not user_input or not user_input.isdigit():
        return None
    choice = int(user_input)
    if 1 <= choice <= len(state.options):
        return state.options[choice - 1].value
    return None


def _edit_columns() -> list[TableColumnSpec[ConfigEntry | str]]:
    def _entry_from(option: SelectOption[ConfigEntry | str]) -> ConfigEntry | None:
        return option.value if isinstance(option.value, ConfigEntry) else None

    def _value_for(option: SelectOption[ConfigEntry | str]) -> str:
        entry = _entry_from(option)
        return entry.value if entry else ""

    def _source_for(option: SelectOption[ConfigEntry | str]) -> str:
        entry = _entry_from(option)
        return entry.source if entry else ""

    return [
        TableColumnSpec(
            header="Key",
            width=22,
            render=lambda opt, _state, _idx, styles, _theme: Text(
                strip_ansi(opt.label), style=styles.label_style
            ),
        ),
        TableColumnSpec(
            header="Value",
            render=lambda opt, _state, _idx, styles, _theme: Text(
                _value_for(opt),
                style=styles.row_style,
            ),
        ),
        TableColumnSpec(
            header="Description",
            render=lambda opt, _state, _idx, styles, _theme: Text(
                strip_ansi(opt.description or ""), style=styles.row_style
            ),
        ),
        TableColumnSpec(
            header="Source",
            width=10,
            render=lambda opt, _state, _idx, styles, _theme: Text(
                _source_for(opt),
                style=styles.row_style,
            ),
        ),
    ]


def _edit_entry(entry: ConfigEntry, global_path: Path) -> None:
    if not entry.env_key or entry.min_value is None:
        console.print("[yellow]Selected setting is read-only.[/yellow]")
        return

    new_value = _prompt_int_value(
        label=entry.key,
        min_value=entry.min_value,
    )
    if new_value is None:
        return

    body = (
        f"Current value: {entry.value}\n"
        f"New value: {new_value}\n\n"
        "Note: increasing this value may increase cost or runtime."
    )
    if not modal_confirm(title="Apply change?", body=body, variant="warn"):
        console.print("[yellow]No changes made.[/yellow]")
        return

    set_env_value(global_path, entry.env_key, str(new_value))
    console.print(f"[bold green]✅ {entry.key} updated.[/bold green]")


def _prompt_int_value(*, label: str, min_value: int) -> int | None:
    while True:
        raw_value = prompt(f"Enter new value for {label} (min {min_value})").strip()
        if not raw_value:
            console.print("[yellow]No changes made.[/yellow]")
            return None
        if not raw_value.isdigit():
            console.print("[red]Please enter a valid integer.[/red]")
            continue
        value = int(raw_value)
        if value < min_value:
            console.print(f"[red]{label} must be at least {min_value}.[/red]")
            continue
        return value
