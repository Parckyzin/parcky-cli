from __future__ import annotations

import contextlib
import os
from pathlib import Path

import typer
from rich.text import Text

from ai_cli.config import loader
from ai_cli.config.paths import get_global_env_path
from ai_cli.config.settings import ConfigEntry, list_config_entries, needs_init
from ai_cli.config.writer import (
    read_ai_provider,
    read_env_value,
    set_ai_provider,
    set_env_value,
    set_provider_api_key,
)
from ai_cli.core.common.enums import AvailableProviders
from ai_cli.core.exceptions import AICliError
from ai_cli.infrastructure.model_catalog import ModelCatalog

from ..ui.components.inputs.numeric import numeric_input
from ..ui.components.modal import confirm as modal_confirm
from ..ui.components.select import SelectOption, SelectState, select
from ..ui.components.theme import DEFAULT_THEME
from ..ui.console import console
from ..ui.errors import exit_with_error, exit_with_unexpected_error
from ..ui.model_select import interactive_model_select
from ..ui.prompts import confirm, prompt, secret_prompt
from ..ui.provider_select import select_provider as prompt_provider_select
from ..ui.renderers.frame import TEXT_FALLBACK_FOOTER, render_frame
from ..ui.renderers.plain_table import render_plain_table
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
            False,
            "--select-model",
            "--select",
            "-s",
            help="Interactive model selection (aliases: --select, -s)",
        ),
        select_provider: bool = typer.Option(
            False, "--provider", "-p", help="Select AI provider"
        ),
        action: str | None = typer.Argument(
            None, help="Optional action (provider, init)"
        ),
    ) -> None:
        """
        🔧 Show ai-cli configuration (read-only).

        Examples:
            ai-cli config                    # Show current config
            ai-cli config -e                 # Edit mode (coming soon)
            ai-cli config init               # Run onboarding wizard
        """
        debug = False
        try:
            settings_dict = loader.build_settings_dict()
            debug = bool(settings_dict.get("debug", False))
            global_path = get_global_env_path()

            if action == "init":
                _run_init_flow(global_path)
                _show_config_status(global_path)
                return

            if needs_init():
                _run_init_flow(global_path)
                if edit:
                    _run_edit_flow(global_path)
                    return
                _show_config_status(global_path)
                return

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
                if not _ensure_provider_key(selected, global_path):
                    return
                set_ai_provider(global_path, selected)
                set_env_value(global_path, "AI_MODEL", "")
                set_env_value(global_path, "MODEL_NAME", "")
                console.print(
                    f"[bold green]✅ Provider set to:[/bold green] {selected}"
                )
                console.print(f"[dim]   Saved to: {global_path}[/dim]")
                return

            if select_model:
                _run_select_model(global_path)
                return

            if set_model or action:
                console.print(
                    "[yellow]Config is read-only. Use parcky-cli config -e to edit.[/yellow]"
                )

            _show_config_status(global_path)
        except AICliError as exc:
            exit_with_error(exc, debug=debug)
        except (KeyboardInterrupt, typer.Abort):
            console.print("[yellow]Cancelled.[/yellow]")
            return
        except typer.Exit:
            raise
        except Exception as exc:
            exit_with_unexpected_error(exc, debug=debug)


def _show_config_status(global_path: Path) -> None:
    """Show current configuration status."""
    rows = list_config_entries(global_path)
    table_rows = [
        [
            entry.key,
            entry.value,
            "yes" if entry.editable else "no",
            entry.source,
        ]
        for entry in rows
    ]
    body = render_plain_table(
        ["Key", "Value", "Editable", "Source"],
        table_rows,
    )

    footer_lines = ["To edit editable values, run: config -e"]
    if needs_init():
        footer_lines.append("To initialize, run: config init")

    output = "\n".join(
        [
            "parcky-cli / config",
            "",
            body,
            "",
            "\n".join(footer_lines),
        ]
    )
    console.print(output)


def _run_init_flow(global_path: Path) -> None:
    console.print("[bold]🔧 Config Init[/bold]")
    console.print("[dim]Let's set up the essentials.[/dim]\n")

    if not _configure_provider_keys(global_path):
        console.print("[yellow]Init cancelled.[/yellow]")
        return

    provider = _select_active_provider(global_path)
    if not provider:
        console.print("[yellow]Init cancelled.[/yellow]")
        return

    model_name = _select_model_name(provider)
    if not model_name:
        console.print("[yellow]Init cancelled.[/yellow]")
        return

    ai_limit = _prompt_numeric_overlay(
        title="AI limits",
        label="ai_max_context_chars",
        min_value=1000,
        default=_current_int_value(global_path, "AI_MAX_CONTEXT_CHARS", 35000),
    )
    if ai_limit is None:
        console.print("[yellow]Init cancelled.[/yellow]")
        return

    git_limit = _prompt_numeric_overlay(
        title="Git limits",
        label="git_max_diff_size",
        min_value=100,
        default=_current_int_value(global_path, "GIT_MAX_DIFF_SIZE", 10000),
    )
    if git_limit is None:
        console.print("[yellow]Init cancelled.[/yellow]")
        return

    summary = (
        f"Provider: {provider}\n"
        f"Model: {model_name}\n"
        f"ai_max_context_chars: {ai_limit}\n"
        f"git_max_diff_size: {git_limit}"
    )
    if not modal_confirm(title="Apply settings?", body=summary, variant="info"):
        console.print("[yellow]No changes made.[/yellow]")
        return

    set_ai_provider(global_path, provider)
    set_env_value(global_path, "AI_MODEL", model_name)
    set_env_value(global_path, "AI_MAX_CONTEXT_CHARS", str(ai_limit))
    set_env_value(global_path, "GIT_MAX_DIFF_SIZE", str(git_limit))
    console.print("[bold green]✅ Configuration saved.[/bold green]")


def _run_select_model(global_path: Path) -> None:
    provider_value = read_ai_provider(global_path)
    if not provider_value:
        console.print(
            "[yellow]No provider configured. Run: parcky-cli config init[/yellow]"
        )
        return

    try:
        provider = AvailableProviders(provider_value)
    except ValueError:
        console.print(
            "[yellow]Unknown provider configured. Run: parcky-cli config init[/yellow]"
        )
        return

    api_key = _resolve_provider_api_key(provider)
    if provider.needs_api_key() and not api_key:
        console.print(
            f"[yellow]No API key set for {provider.value}. "
            "Run: parcky-cli config init[/yellow]"
        )
        return

    catalog = ModelCatalog()
    try:
        models = catalog.list_models(provider, api_key)
    except AICliError as exc:
        console.print(f"[yellow]Warning:[/yellow] {exc.user_message}")
        models = []

    current_model = (
        read_env_value(global_path, "AI_MODEL")
        or read_env_value(global_path, "MODEL_NAME")
        or ""
    )

    selected: list[str] = []

    def _on_select(model: str) -> None:
        selected.append(model)
        set_env_value(global_path, "AI_MODEL", model)

    interactive_model_select(
        models,
        current_model,
        _on_select,
        current_provider=provider,
        on_change_provider=None,
    )
    if selected:
        console.print(f"[bold green]✅ Model set to:[/bold green] {selected[0]}")


def _configure_provider_keys(global_path: Path) -> bool:
    providers = [p for p in AvailableProviders if p.needs_api_key()]
    while True:
        options: list[SelectOption[AvailableProviders | str]] = []
        has_any_key = False
        for provider in providers:
            status = "set" if _has_provider_key(provider, global_path) else "missing"
            if status == "set":
                has_any_key = True
            options.append(
                SelectOption(
                    value=provider,
                    label=provider,
                    description=f"API key {status}",
                )
            )
        if has_any_key:
            options.append(
                SelectOption(
                    value="Remove key",
                    label="Remove key",
                    description="Delete a saved API key",
                )
            )
        options.append(
            SelectOption(value="Continue", label="Continue", description=None)
        )

        selection = _select_option(options, "Manage API keys")
        if selection is None:
            return False
        if selection == "Continue":
            return True
        if selection == "Remove key":
            if not _remove_provider_key_flow(global_path):
                return False
            continue
        if isinstance(selection, AvailableProviders) and not _set_provider_key(
            selection, global_path
        ):
            return False


def _set_provider_key(provider: AvailableProviders, global_path: Path) -> bool:
    new_key = secret_prompt(f"Enter {provider.value} API key").strip()
    if not new_key:
        console.print("[yellow]Cancelled.[/yellow]")
        return False
    set_provider_api_key(global_path, provider, new_key)
    console.print(f"[bold green]✅ {provider.value} key saved.[/bold green]")
    return True


def _remove_provider_key_flow(global_path: Path) -> bool:
    providers = [
        provider
        for provider in AvailableProviders
        if provider.needs_api_key() and _has_provider_key(provider, global_path)
    ]
    if not providers:
        console.print("[yellow]No API keys to remove.[/yellow]")
        return True
    options: list[SelectOption[AvailableProviders | str]] = [
        SelectOption(
            value=provider,
            label=provider,
            description="API key set",
        )
        for provider in providers
    ]
    options.append(SelectOption(value="Back", label="Back", description="Return"))
    selection = _select_option(options, "Remove API key")
    if selection is None:
        return False
    if selection == "Back":
        return True
    if isinstance(selection, AvailableProviders):
        body = f"Remove saved API key for {selection.value}?"
        if not modal_confirm(title="Remove API key?", body=body, variant="warn"):
            console.print("[yellow]Cancelled.[/yellow]")
            return False
        set_env_value(global_path, selection.env_api_key_name(), "")
        console.print(f"[bold green]✅ {selection.value} key removed.[/bold green]")
    return True


def _select_active_provider(global_path: Path) -> str | None:
    while True:
        ready = _ready_providers(global_path)
        if not ready:
            console.print(
                render_frame(
                    title="Select provider",
                    body=Text(
                        "No providers are ready. Add an API key to continue.",
                        style=DEFAULT_THEME.frame_warn_style,
                    ),
                    footer="Redirecting to Manage API keys...",
                )
            )
            if not _configure_provider_keys(global_path):
                return None
            ready = _ready_providers(global_path)
            if not ready:
                return None

        current_provider = read_ai_provider(global_path) or None
        options = [
            SelectOption(
                value=provider.value,
                label=provider.value,
                description=None,
                is_current=provider.value == (current_provider or ""),
            )
            for provider in ready
        ]
        selected = select(options, title="Select provider")
        if not selected:
            return None
        if _ensure_provider_key(selected, global_path):
            return selected


def _select_model_name(provider: str) -> str | None:
    try:
        provider_enum = AvailableProviders(provider)
    except ValueError:
        console.print("[yellow]Unknown provider.[/yellow]")
        return None

    api_key = _resolve_provider_api_key(provider_enum)
    if provider_enum.needs_api_key() and not api_key:
        console.print(
            f"[yellow]No API key set for {provider_enum.value}. "
            "Add one to list models.[/yellow]"
        )
        return None

    catalog = ModelCatalog()
    try:
        models = catalog.list_models(provider_enum, api_key)
    except AICliError as exc:
        console.print(f"[yellow]Warning:[/yellow] {exc.user_message}")
        models = []

    if not models:
        console.print("[yellow]No models available.[/yellow]")
        return None

    options = [
        SelectOption(value=model, label=model, description=None) for model in models
    ]
    selection = select(options, title="Select model")
    if selection is None:
        return None
    return str(selection)


def _current_int_value(path: Path, env_key: str, fallback: int) -> int:
    raw = read_env_value(path, env_key)
    if raw.isdigit():
        return int(raw)
    return fallback


def _select_option(
    options: list[SelectOption[AvailableProviders | str]],
    title: str,
) -> AvailableProviders | str | None:
    try:
        return select(options, title=title)
    except ImportError:
        console.print(
            "[yellow]prompt_toolkit not available. Using text fallback.[/yellow]"
        )
    except Exception as exc:
        console.print(
            f"[yellow]Interactive UI failed ({exc}). Using text fallback.[/yellow]"
        )

    state = SelectState.from_options(options)
    console.print(
        render_frame(
            title=title,
            body=render_table(state, title=None, show_index=True),
            footer=TEXT_FALLBACK_FOOTER,
        )
    )
    user_input = prompt("Enter number or blank to cancel").strip()
    if not user_input or not user_input.isdigit():
        return None
    choice = int(user_input)
    if 1 <= choice <= len(options):
        return options[choice - 1].value
    return None


def _ensure_provider_key(provider: str, global_path: Path) -> bool:
    try:
        provider_enum = AvailableProviders(provider)
    except ValueError:
        return True

    if not provider_enum.needs_api_key():
        return True

    if _has_provider_key(provider_enum, global_path):
        return True

    console.print(
        f"[yellow]No API key set for {provider_enum.value}. "
        "Add one to use this provider.[/yellow]"
    )
    if not confirm("Add API key now?", default=True):
        return False
    new_key = prompt(f"Enter {provider_enum.value} API key").strip()
    if not new_key:
        console.print("[yellow]No API key provided. Cancelled.[/yellow]")
        return False
    set_provider_api_key(global_path, provider_enum, new_key)
    return True


def _has_provider_key(provider: AvailableProviders, global_path: Path) -> bool:
    env_key = provider.env_api_key_name()
    if read_env_value(global_path, env_key):
        return True
    if read_env_value(global_path, "AI_API_KEY"):
        return True
    return provider == AvailableProviders.GOOGLE and bool(
        read_env_value(global_path, "GEMINI_API_KEY")
    )


def _resolve_provider_api_key(provider: AvailableProviders) -> str | None:
    values = loader.load_settings_values()
    env_key = provider.env_api_key_name()
    direct = values.get(env_key)
    if direct:
        return str(direct).strip() or None
    legacy = values.get("AI_API_KEY")
    if legacy:
        return str(legacy).strip() or None
    if provider == AvailableProviders.GOOGLE:
        gemini = values.get("GEMINI_API_KEY")
        if gemini:
            return str(gemini).strip() or None
    return None


def _ready_providers(global_path: Path) -> list[AvailableProviders]:
    ready: list[AvailableProviders] = []
    for provider in AvailableProviders:
        if not provider.needs_api_key():
            ready.append(provider)
            continue
        if _has_provider_key(provider, global_path):
            ready.append(provider)
    return ready


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
        console.print(
            "[yellow]prompt_toolkit not available. Using text fallback.[/yellow]"
        )
    except Exception as exc:
        console.print(
            f"[yellow]Interactive UI failed ({exc}). Using text fallback.[/yellow]"
        )

    state = SelectState.from_options(options)
    console.print(
        render_frame(
            title="Edit configuration",
            body=render_table(state, title=None, show_index=True),
            footer=TEXT_FALLBACK_FOOTER,
        )
    )
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
    try:
        return select(options, title=title)
    except ImportError:
        console.print(
            "[yellow]prompt_toolkit not available. Using text fallback.[/yellow]"
        )
    except Exception as exc:
        console.print(
            f"[yellow]Interactive UI failed ({exc}). Using text fallback.[/yellow]"
        )

    headers = ["Key", "Value", "Description", "Source"]
    rows = [
        [entry.key, entry.value, entry.description, entry.source]
        if isinstance(entry, ConfigEntry)
        else ["Back", "", "", ""]
        for entry in [opt.value for opt in options]
    ]
    console.print(
        "\n".join(
            [
                title,
                "",
                render_plain_table(headers, rows),
                "",
                TEXT_FALLBACK_FOOTER,
            ]
        )
    )
    user_input = prompt("Enter number or blank to cancel").strip()
    if not user_input or not user_input.isdigit():
        return None
    choice = int(user_input)
    if 1 <= choice <= len(options):
        return options[choice - 1].value
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

    current_value = int(entry.value) if entry.value.isdigit() else None
    new_value = numeric_input(
        title="Edit setting",
        context=None,
        label=entry.key,
        current_value=current_value,
        min_value=entry.min_value,
        max_value=None,
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


def _prompt_numeric_overlay(
    *,
    title: str,
    label: str,
    min_value: int,
    default: int | None = None,
) -> int | None:
    body = Text.assemble(
        ("Enter a value for ", "dim"),
        (label, "bold"),
        (f" (min {min_value})", "dim"),
    )
    if default is not None:
        body = Text.assemble(
            body,
            Text(f"\nDefault: {default}", style="dim"),
        )

    return numeric_input(
        title=title,
        context=None,
        label=f"Enter value for {label}",
        current_value=default,
        min_value=min_value,
        max_value=None,
    )
