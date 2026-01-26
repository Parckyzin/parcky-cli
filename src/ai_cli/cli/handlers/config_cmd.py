from __future__ import annotations

import contextlib
import os
from pathlib import Path

import typer

from ai_cli.clients import get_ai_service
from ai_cli.config import loader
from ai_cli.config.paths import get_global_env_path, get_local_env_path
from ai_cli.config.settings import AIConfig, AppConfig, GitConfig
from ai_cli.config.writer import (
    read_ai_provider,
    read_env_value,
    set_ai_provider,
    set_config_value,
    set_env_value,
)
from ai_cli.core.exceptions import AICliError

from ..context import get_context
from ..ui.console import console
from ..ui.errors import exit_with_error, exit_with_unexpected_error
from ..ui.model_select import interactive_model_select
from ..ui.panels import config_settings_table
from ..ui.provider_select import select_provider as prompt_provider_select
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
        set_model: str = typer.Option(
            None, "--model", "-m", help="Set the AI model to use"
        ),
        use_global: bool = typer.Option(
            False, "--global", "-g", help="Apply changes to global config"
        ),
        select_model: bool = typer.Option(
            False, "--select", "-s", help="Interactive model selection"
        ),
        select_provider: bool = typer.Option(
            False, "--provider", "-p", help="Select AI provider"
        ),
        action: str | None = typer.Argument(
            None, help="Optional action (provider)"
        ),
    ) -> None:
        """
        🔧 Show or update ai-cli configuration.

        Examples:
            ai-cli config                    # Show current config
            ai-cli config --select           # Interactive model selection
            ai-cli config --provider         # Interactive provider selection
            ai-cli config --model gemini-2.0-flash  # Change model directly
            ai-cli config --model gemini-2.0-flash --global  # Change model globally
            ai-cli config provider           # Interactive provider selection
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

            select_provider_flag = select_provider or action == "provider"

            if select_provider_flag:
                current_provider = read_ai_provider(active_path) or ""
                selected = prompt_provider_select(current=current_provider or None)
                if not selected:
                    console.print("[yellow]Cancelled.[/yellow]")
                    return
                set_ai_provider(active_path, selected)
                set_env_value(active_path, "AI_MODEL", "")
                set_env_value(active_path, "MODEL_NAME", "")
                console.print(
                    f"[bold green]✅ Provider set to:[/bold green] {selected}"
                )
                console.print(f"[dim]   Saved to: {active_path}[/dim]")
                return

            if select_model:
                current_model = (
                    read_env_value(active_path, "AI_MODEL")
                    or read_env_value(active_path, "MODEL_NAME")
                    or "gemini-2.0-flash"
                )
                try:
                    models = ctx.ai_service.get_available_models()
                except AICliError as exc:
                    console.print(
                        f"[yellow]Warning:[/yellow] {exc.user_message or str(exc)}"
                    )
                    models = []
                except Exception:
                    console.print(
                        "[yellow]Warning:[/yellow] Unable to load models. Manual mode enabled."
                    )
                    models = []

                def _on_select(model: str) -> None:
                    set_env_value(active_path, "AI_MODEL", model)

                def _on_change_provider(
                    provider: str,
                ) -> tuple[list[str], str | None]:
                    set_ai_provider(active_path, provider)
                    set_env_value(active_path, "AI_MODEL", "")
                    set_env_value(active_path, "MODEL_NAME", "")
                    try:
                        new_config = AppConfig.load()
                        new_service = get_ai_service(new_config.ai)
                        return new_service.get_available_models(), ""
                    except AICliError as exc:
                        console.print(
                            f"[yellow]Warning:[/yellow] {exc.user_message or str(exc)}"
                        )
                        return [], ""
                    except Exception:
                        console.print(
                            "[yellow]Warning:[/yellow] Unable to load models. Manual mode enabled."
                        )
                        return [], ""

                current_provider = read_ai_provider(active_path) or None
                interactive_model_select(
                    models,
                    current_model,
                    _on_select,
                    current_provider=current_provider,
                    on_change_provider=_on_change_provider,
                )
                return

            if set_model:
                set_env_value(active_path, "AI_MODEL", set_model)
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
    config_snapshot = _load_config_snapshot()

    active_path = local_path if local_path.exists() else global_path
    active_label = "local" if local_path.exists() else "global"

    api_key = read_env_value(active_path, "AI_API_KEY") or read_env_value(
        active_path, "GEMINI_API_KEY"
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
        console.print(f"  [dim]✗[/dim] Global: {global_path} [dim](not found)[/dim]")

    if local_path.exists():
        console.print(f"  [green]✓[/green] Local:  {local_path.absolute()}")
        console.print("    [dim](takes priority over global)[/dim]")
    else:
        console.print("[dim]  ✗ Local:  .env (not found)[/dim]")

    console.print("\n[dim]Commands:[/dim]")
    console.print("  ai-cli setup              [dim]# Change API key[/dim]")
    console.print("  ai-cli config -s          [dim]# Select model (interactive)[/dim]")
    console.print("  ai-cli config -m MODEL    [dim]# Set model directly[/dim]")

    rows = _build_config_rows(config_snapshot, local_path, global_path)
    console.print("\n[bold]Editable Settings:[/bold]")
    console.print(config_settings_table(rows))

    _prompt_edit_setting(rows, active_path)


def _build_config_rows(
    config: tuple[AIConfig, GitConfig], local_path: Path, global_path: Path
) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    ai_config, git_config = config

    rows.append(
        (
            "ai_max_context_chars",
            str(ai_config.max_context_chars),
            loader.resolve_setting_source(
                ["AI_MAX_CONTEXT_CHARS"], local_path, global_path
            ),
            "Max chars sent to AI context",
        )
    )
    rows.append(
        (
            "git_max_diff_size",
            str(git_config.max_diff_size),
            loader.resolve_setting_source(
                ["GIT_MAX_DIFF_SIZE"], local_path, global_path
            ),
            "Max diff size for AI analysis",
        )
    )
    rows.append(
        (
            "ai_system_instruction",
            _truncate(ai_config.system_instruction or "", 40),
            loader.resolve_setting_source(
                ["AI_SYSTEM_INSTRUCTION"], local_path, global_path
            ),
            "System prompt (read-only)",
        )
    )
    rows.append(
        (
            "model",
            ai_config.model_name,
            loader.resolve_setting_source(
                ["AI_MODEL", "MODEL_NAME"], local_path, global_path
            ),
            "AI model name (read-only)",
        )
    )
    return rows


def _prompt_edit_setting(rows: list[tuple[str, str, str, str]], path: Path) -> None:
    key_map = {1: "ai_max_context_chars", 2: "git_max_diff_size"}
    max_index = len(rows)
    while True:
        selection = prompt(
            "Select setting to edit (1-2) or press Enter to exit"
        ).strip()
        if not selection:
            return
        if not selection.isdigit():
            console.print("[red]Invalid choice. Enter a number.[/red]")
            continue
        index = int(selection)
        if index < 1 or index > max_index:
            console.print("[red]Invalid selection.[/red]")
            continue
        if index not in key_map:
            console.print("[yellow]Selected setting is read-only.[/yellow]")
            return

        key = key_map[index]
        if key == "ai_max_context_chars":
            _edit_int_setting(
                path,
                env_key="AI_MAX_CONTEXT_CHARS",
                label="ai_max_context_chars",
                min_value=1000,
            )
            return
        if key == "git_max_diff_size":
            _edit_int_setting(
                path,
                env_key="GIT_MAX_DIFF_SIZE",
                label="git_max_diff_size",
                min_value=100,
            )
            return


def _edit_int_setting(
    path: Path,
    *,
    env_key: str,
    label: str,
    min_value: int,
) -> None:
    while True:
        raw_value = prompt(f"Enter new value for {label} (min {min_value})").strip()
        if not raw_value:
            console.print("[yellow]No changes made.[/yellow]")
            return
        if not raw_value.isdigit():
            console.print("[red]Please enter a valid integer.[/red]")
            continue
        value = int(raw_value)
        if value < min_value:
            console.print(
                f"[red]{label} must be at least {min_value}.[/red]"
            )
            continue
        set_config_value(path, env_key, value)
        console.print(f"[bold green]✅ {label} updated.[/bold green]")
        return


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def _load_config_snapshot() -> tuple[AIConfig, GitConfig]:
    settings_dict = loader.build_settings_dict()
    ai_values = settings_dict.get("ai", {})
    git_values = settings_dict.get("git", {})
    ai_config = AIConfig.model_construct(**ai_values)
    git_config = GitConfig.model_construct(**git_values)
    return ai_config, git_config
