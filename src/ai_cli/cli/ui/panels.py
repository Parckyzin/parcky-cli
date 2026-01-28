from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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


def config_settings_table(rows: list[tuple[str, str, str, str]]) -> Table:
    """Build a settings table for config display."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Key", no_wrap=True, width=22)
    table.add_column("Value")
    table.add_column("Source", width=10)
    table.add_column("Description")

    for idx, (key, value, source, description) in enumerate(rows, start=1):
        table.add_row(str(idx), key, value, source, description)

    return table
