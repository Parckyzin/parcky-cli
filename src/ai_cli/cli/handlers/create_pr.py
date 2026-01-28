from __future__ import annotations

import typer

from ai_cli.core.exceptions import AICliError, PullRequestError
from ai_cli.services.create_pr_service import CreatePRService

from ..context import get_context
from ..ui.console import console
from ..ui.errors import exit_with_error, exit_with_unexpected_error
from ..ui.panels import pull_request_preview_panel
from ..ui.prompts import confirm


def register(app: typer.Typer) -> None:
    """Register create-pr command."""

    @app.command()
    def create_pr(
        base: str = typer.Option(
            None,
            "--base",
            "-b",
            help="Base branch to create PR against (default: main/master)",
        ),
        auto_confirm: bool = typer.Option(
            False, "--yes", "-y", help="Auto-confirm PR creation"
        ),
    ) -> None:
        """
        📋 Create a Pull Request based on current branch changes.

        This command will:
        1. 🔍 Analyze commits on the current branch
        2. 📊 Compare changes against base branch (main/master)
        3. 🤖 Generate PR title and description using AI
        4. 📋 Create the Pull Request on GitHub

        Examples:
            ai-cli create-pr
            ai-cli create-pr --base develop
            ai-cli create-pr --yes
        """
        debug = False
        try:
            ctx = get_context()
            debug = ctx.config.debug
            if not ctx.pr_service:
                raise PullRequestError(
                    "Pull request service unavailable.",
                    user_message=(
                        "GitHub CLI is not available. Install it and run "
                        "`gh auth login`."
                    ),
                )

            service = CreatePRService(
                git_repo=ctx.git_repo,
                ai_service=ctx.ai_service,
                pr_service=ctx.pr_service,
                max_context_chars=ctx.config.ai.max_context_chars,
            )

            console.print("[yellow]🔍 Analyzing branch changes...[/yellow]")
            branch_info = service.get_branch_info(base)

            console.print(f"\n[bold]Branch:[/bold] {branch_info.name}")
            console.print(f"[bold]Base:[/bold] {branch_info.base_branch}")
            console.print(f"[bold]Commits:[/bold] {len(branch_info.commits)}")
            console.print(
                f"[bold]Files Changed:[/bold] {len(branch_info.files_changed)}"
            )

            if branch_info.commits:
                console.print("\n[bold]📝 Commits:[/bold]")
                for commit in branch_info.commits[:10]:
                    console.print(f"  • {commit}")
                if len(branch_info.commits) > 10:
                    console.print(
                        f"  [dim]... and {len(branch_info.commits) - 10} more[/dim]"
                    )

            if branch_info.files_changed:
                console.print("\n[bold]📁 Files Changed:[/bold]")
                for file_path in branch_info.files_changed[:10]:
                    console.print(f"  • {file_path}")
                if len(branch_info.files_changed) > 10:
                    console.print(
                        f"  [dim]... and {len(branch_info.files_changed) - 10} more[/dim]"
                    )

            console.print("\n[yellow]🤖 Generating PR content with AI...[/yellow]")
            pr = service.generate_pr_content(branch_info)

            console.print(pull_request_preview_panel(pr))

            if not auto_confirm and not confirm("\n🚀 Create this Pull Request?"):
                console.print("[yellow]ℹ️  PR creation cancelled.[/yellow]")
                raise typer.Exit(0) from None

            console.print("\n[yellow]📤 Creating Pull Request...[/yellow]")
            ctx.pr_service.create_pull_request(pr)
            console.print(
                "[bold green]✅ Pull Request created successfully![/bold green]"
            )

        except AICliError as exc:
            exit_with_error(exc, debug=debug)
        except Exception as exc:
            exit_with_unexpected_error(exc, debug=debug)
