from __future__ import annotations

import typer

from ai_cli.core.exceptions import AICliError
from ai_cli.services.smart_commit_all_service import SmartCommitAllService

from ..context import get_context
from ..ui.console import console
from ..ui.errors import exit_with_error, exit_with_unexpected_error
from ..ui.prompts import confirm


def register(app: typer.Typer) -> None:
    """Register smart-commit-all command."""

    @app.command()
    def smart_commit_all(
        push: bool = typer.Option(
            True, "--push/--no-push", help="Push changes to remote repository"
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Preview actions without modifying git"
        ),
        explain: bool = typer.Option(
            False, "--explain", help="Explain how files were grouped"
        ),
        auto_confirm: bool = typer.Option(
            False, "--yes", "-y", help="Auto-confirm all prompts"
        ),
    ) -> None:
        """
        🚀 Commit ALL changes in the project with smart grouping.

        This command will:
        1. 🔍 Find all changed files in the repository
        2. 📁 Group files by folder
        3. 🔗 Analyze file correlation within each folder
        4. 🤖 Generate commit messages for each group
        5. 📦 Create separate commits for each group
        6. 🚀 Push to remote (if --push, default: true)

        Files in the same folder that are related (e.g., a module and its tests)
        will be committed together. Unrelated files will be committed separately.
        """
        debug = False
        try:
            ctx = get_context()
            debug = ctx.config.debug
            service = SmartCommitAllService(
                git_repo=ctx.git_repo, ai_service=ctx.ai_service
            )
            console.print("[yellow]🔍 Scanning for all changes...[/yellow]")
            plan = service.plan_smart_commit_all()

            if plan.total_files == 0:
                console.print(
                    "[bold yellow]⚠️  No changes found in the repository.[/bold yellow]"
                )
                raise typer.Exit(0) from None

            console.print(
                f"\n[bold]Found {plan.total_files} changed file(s):[/bold]"
            )
            for change in plan.changes:
                status_icon = {
                    "M": "📝",
                    "A": "➕",
                    "D": "❌",
                    "R": "🔄",
                    "??": "❓",
                }.get(change.status, "📄")
                console.print(f"  {status_icon} {change.path} ({change.status})")

            if not dry_run and not auto_confirm and not confirm(
                "\n✅ Proceed with smart commit all?"
            ):
                console.print("[yellow]ℹ️  Operation cancelled.[/yellow]")
                raise typer.Exit(0) from None

            console.print("\n[yellow]🤖 Analyzing and grouping files...[/yellow]")
            result = service.execute_smart_commit_all(
                auto_push=push,
                dry_run=dry_run,
                plan=plan,
            )

            if result.dry_run:
                console.print(
                    "[bold cyan]🧪 DRY RUN[/bold cyan] No git changes applied."
                )

            console.print("\n[bold]📊 Commit Summary:[/bold]")
            for commit in result.commit_results:
                if commit.status == "success":
                    console.print(
                        f"\n[green]✅ {commit.group.folder}/[/green] "
                        f"({commit.group.file_count} file(s))"
                    )
                    console.print(f"   [dim]Message:[/dim] {commit.commit_message}")
                    if explain and commit.group.explanation:
                        console.print(
                            f"   [dim]Why:[/dim] {commit.group.explanation}"
                        )
                    for file_path in commit.group.file_paths:
                        console.print(f"   • {file_path}")
                elif commit.status == "planned":
                    console.print(
                        f"\n[cyan]📝 {commit.group.folder}/[/cyan] "
                        f"({commit.group.file_count} file(s))"
                    )
                    console.print(
                        f"   [dim]Planned:[/dim] {commit.commit_message}"
                    )
                    if explain and commit.group.explanation:
                        console.print(
                            f"   [dim]Why:[/dim] {commit.group.explanation}"
                        )
                    for file_path in commit.group.file_paths:
                        console.print(f"   • {file_path}")
                else:
                    console.print(
                        f"\n[red]❌ {commit.group.folder}/[/red] - {commit.error}"
                    )

            console.print("\n" + "─" * 50)
            console.print(
                f"[bold]Total:[/bold] {result.total_files} files in "
                f"{result.total_groups} groups"
            )
            console.print(
                f"[green]Successful:[/green] {result.successful_commits} | "
                f"[red]Failed:[/red] {result.failed_commits}"
            )

            if result.pushed:
                console.print(
                    "[bold green]✅ All changes pushed successfully![/bold green]"
                )
            elif push and result.successful_commits > 0 and not result.dry_run:
                console.print("[bold yellow]⚠️  Push failed[/bold yellow]")

        except AICliError as exc:
            exit_with_error(exc, debug=debug)
        except Exception as exc:
            exit_with_unexpected_error(exc, debug=debug)
