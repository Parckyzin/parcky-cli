from __future__ import annotations

import typer

from ai_cli.core.common.enums import RepositoryVisibility
from ai_cli.core.exceptions import AICliError, UsageError
from ai_cli.core.models import Repository
from ai_cli.infrastructure.repo_service import GitHubRepoService

from ..context import get_context
from ..ui.console import console
from ..ui.errors import exit_with_error, exit_with_unexpected_error


def register(app: typer.Typer) -> None:
    """Register create-repo command."""

    @app.command()
    def create_repo(
        name: str = typer.Argument(..., help="Name of the repository to create"),
        visibility: str = typer.Option(
            "private",
            "--visibility",
            "-v",
            help="Repository visibility: public, private, or internal",
        ),
        description: str = typer.Option(
            "",
            "--description",
            "-d",
            help="Repository description",
        ),
    ) -> None:
        """
        📁 Create a new GitHub repository.

        This command will create a new repository on GitHub using the GitHub CLI.

        Examples:
            ai-cli create-repo my-new-project
            ai-cli create-repo my-app -v public -d "My awesome application"
        """
        debug = False
        try:
            ctx = get_context()
            debug = ctx.config.debug
            try:
                repo_visibility = RepositoryVisibility(visibility.lower())
            except ValueError as err:
                raise UsageError(
                    f"Invalid visibility '{visibility}'.",
                    user_message=(
                        "Invalid visibility value. Use one of: public, private, internal."
                    ),
                ) from err

            console.print(f"[yellow]📁 Creating repository '{name}'...[/yellow]")

            repo_service = GitHubRepoService()
            repo = Repository(
                name=name,
                visibility=repo_visibility,
                description=description,
            )

            url = repo_service.create_repository(repo)

            console.print(
                "[bold green]✅ Repository created successfully![/bold green]"
            )
            console.print(f"[blue]🔗 URL: {url}[/blue]")

        except AICliError as exc:
            exit_with_error(exc, debug=debug)
        except Exception as exc:
            exit_with_unexpected_error(exc, debug=debug)
