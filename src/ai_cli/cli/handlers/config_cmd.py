from __future__ import annotations

import contextlib
import os
from pathlib import Path

import typer

from ai_cli.config.paths import get_global_env_path, get_local_env_path
from ai_cli.config.writer import read_env_value, set_env_value
from ai_cli.core.exceptions import AICliError

from ..context import get_context
from ..ui.console import console
from ..ui.errors import exit_with_error, exit_with_unexpected_error
from ..ui.model_select import interactive_model_select
from ..ui.prompts import confirm, prompt


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
            console.print(
                f"[bold green]✅ API key saved to {global_path}[/bold green]"
            )
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
        set_model: str = typer.Option(
            None, "--model", "-m", help="Set the AI model to use"
        ),
        use_global: bool = typer.Option(
            False, "--global", "-g", help="Apply changes to global config"
        ),
        select_model: bool = typer.Option(
            False, "--select", "-s", help="Interactive model selection from history"
        ),
    ) -> None:
        """
        🔧 Show or update ai-cli configuration.

        Examples:
            ai-cli config                    # Show current config
            ai-cli config --select           # Interactive model selection
            ai-cli config --model gemini-2.0-flash  # Change model directly
            ai-cli config --model gemini-2.0-flash --global  # Change model globally
        """
        debug = False
        try:
            ctx = get_context()
            debug = ctx.config.debug
            global_path = get_global_env_path()
            local_path = get_local_env_path()

            active_path = (
                local_path if local_path.exists() and not use_global else global_path
            )
            cache = ctx.cache

            if select_model:
                interactive_model_select(active_path, cache)
                return

            if set_model:
                set_env_value(active_path, "AI_MODEL", set_model)
                cache.add_model_to_history(set_model)
                console.print(f"[bold green]✅ Model set to:[/bold green] {set_model}")
                console.print(f"[dim]   Saved to: {active_path}[/dim]")
                return

            _show_config_status(global_path, local_path)
        except AICliError as exc:
            exit_with_error(exc, debug=debug)
        except Exception as exc:
            exit_with_unexpected_error(exc, debug=debug)


def _show_config_status(global_path: Path, local_path: Path) -> None:
    """Show current configuration status."""
    console.print("[bold]🔧 AI CLI Configuration[/bold]\n")

    active_path = local_path if local_path.exists() else global_path
    active_label = "local" if local_path.exists() else "global"

    api_key = (
        read_env_value(active_path, "AI_API_KEY")
        or read_env_value(active_path, "GEMINI_API_KEY")
    )
    model_name = (
        read_env_value(active_path, "AI_MODEL")
        or read_env_value(active_path, "MODEL_NAME")
        or "gemini-2.0-flash"
    )

    console.print("[bold]Current Settings:[/bold]")
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        console.print(f"  API Key: [green]{masked}[/green]")
    else:
        console.print("  API Key: [red]Not set[/red]")

    console.print(f"  Model:   [cyan]{model_name}[/cyan]")
    console.print(f"  Source:  [dim]{active_label} ({active_path})[/dim]")

    console.print("\n[bold]Config Files:[/bold]")
    if global_path.exists():
        console.print(f"  [green]✓[/green] Global: {global_path}")
    else:
        console.print(
            f"  [dim]✗[/dim] Global: {global_path} [dim](not found)[/dim]"
        )

    if local_path.exists():
        console.print(f"  [green]✓[/green] Local:  {local_path.absolute()}")
        console.print("    [dim](takes priority over global)[/dim]")
    else:
        console.print("[dim]  ✗ Local:  .env (not found)[/dim]")

    console.print("\n[dim]Commands:[/dim]")
    console.print("  ai-cli setup              [dim]# Change API key[/dim]")
    console.print("  ai-cli config -s          [dim]# Select model (interactive)[/dim]")
    console.print("  ai-cli config -m MODEL    [dim]# Set model directly[/dim]")
