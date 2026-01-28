from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme
from ai_cli.config.settings import ConfigEntry
from ai_cli.core.models import PullRequest


def commit_preview_panel(commit_message: str) -> Panel:
    """Build the commit preview panel."""
    return Panel(
        Text(commit_message, style="bold green"),
        title="💡 Suggested Commit Message",
        border_style="green",
    )


def pull_request_preview_panel(pr: PullRequest) -> Panel:
    """Build the pull request preview panel."""
    return Panel(
        f"[bold]Title:[/bold] {pr.title}\n\n[bold]Description:[/bold]\n{pr.body}",
        title="📋 Pull Request Preview",
        border_style="blue",
    )


def config_settings_table(
    rows: list[ConfigEntry],
    *,
    theme: Theme = DEFAULT_THEME,
) -> Table:
    """Build a settings table for config display."""
    table = Table(show_header=True, header_style=theme.header_style)
    table.add_column("Key", no_wrap=True, width=24)
    table.add_column("Value")
    table.add_column("Editable", width=9, justify="center")
    table.add_column("Source", width=10)

    for entry in rows:
        editable = "yes" if entry.editable else "no"
        table.add_row(entry.key, entry.value, editable, entry.source)

    return table


def config_hint_panel(message: str, *, theme: Theme = DEFAULT_THEME) -> Panel:
    return Panel(
        Text(message, style=theme.muted_style),
        border_style=theme.muted_style,
        padding=(0, 1),
    )
