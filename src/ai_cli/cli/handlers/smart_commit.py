from __future__ import annotations

import typer

from ai_cli.core.exceptions import AICliError
from ai_cli.services.smart_commit_service import SmartCommitService

from ..context import get_context
from ..ui.console import console
from ..ui.errors import exit_with_error, exit_with_unexpected_error
from ..ui.panels import commit_preview_panel, pull_request_preview_panel
from ..ui.prompts import confirm, prompt


def register(app: typer.Typer) -> None:
    """Register smart-commit command."""

    @app.command()
    def smart_commit(
        push: bool = typer.Option(
            True, "--push/--no-push", help="Push changes to remote repository"
        ),
        pr: bool = typer.Option(
            False, "--pr/--no-pr", help="Create pull request after commit"
        ),
        auto_confirm: bool = typer.Option(
            False, "--yes", "-y", help="Auto-confirm all prompts"
        ),
    ) -> None:
        """
        🚀 Create AI-powered commit with optional push and PR creation.

        This command will:
        1. 🔍 Analyze your staged changes
        2. 🤖 Generate a conventional commit message using AI
        3. 📦 Create the commit
        4. 🚀 Push to remote (if --push, default: true)
        5. 📋 Create pull request (if --pr, default: false)
        """
        debug = False
        try:
            ctx = get_context()
            debug = ctx.config.debug
            service = SmartCommitService(
                git_repo=ctx.git_repo,
                ai_service=ctx.ai_service,
                pr_service=ctx.pr_service,
            )

            console.print("[yellow]🔍 Analyzing staged changes...[/yellow]")

            diff = service.get_staged_changes()

            if diff.is_truncated:
                console.print(
                    "[yellow]⚠️  Large diff detected - truncated for AI analysis[/yellow]"
                )

            console.print("[yellow]🤖 Generating commit message with AI...[/yellow]")
            commit_msg = service.generate_commit_message(diff)

            console.print(commit_preview_panel(commit_msg))

            if not auto_confirm and not confirm("✅ Accept this message?"):
                commit_msg = prompt("📝 Enter your custom message")

            console.print("[yellow]📦 Creating commit...[/yellow]")
            service.create_commit(commit_msg)
            console.print("[bold green]✅ Commit created successfully![/bold green]")

            if push:
                current_branch = ctx.git_repo.get_current_branch()
                console.print(
                    f"[yellow]🚀 Pushing to branch '{current_branch.name}'...[/yellow]"
                )
                service.push_changes(True)
                console.print(
                    "[bold green]✅ Changes pushed successfully![/bold green]"
                )

            if pr:
                if not ctx.pr_service:
                    console.print(
                        "[bold red]❌ Pull Request creation not available. "
                        "Make sure GitHub CLI is installed and configured.[/bold red]"
                    )
                    return

                console.print("[yellow]📋 Generating pull request...[/yellow]")
                pr_data = ctx.ai_service.generate_pull_request(diff, commit_msg)

                console.print(pull_request_preview_panel(pr_data))

                if auto_confirm or confirm("🚀 Create pull request with this content?"):
                    ctx.pr_service.create_pull_request(pr_data)
                    console.print(
                        "[bold green]✅ Pull request created successfully![/bold green]"
                    )
                else:
                    console.print("[yellow]ℹ️  Pull request creation skipped.[/yellow]")

        except AICliError as exc:
            exit_with_error(exc, debug=debug)
        except Exception as exc:
            exit_with_unexpected_error(exc, debug=debug)
