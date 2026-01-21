from rich.panel import Panel
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
