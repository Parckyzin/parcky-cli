"""
Repository service implementation using GitHub CLI.
"""

import subprocess

from ..core.exceptions import RepositoryError
from ..core.interfaces import RepositoryServiceInterface
from ..core.models import Repository


class GitHubRepoService(RepositoryServiceInterface):
    """GitHub repository service using GitHub CLI."""

    def __init__(self) -> None:
        self._check_gh_cli()

    def _check_gh_cli(self) -> None:
        """Check if GitHub CLI is available."""
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RepositoryError(
                "GitHub CLI (gh) is not installed or not available. "
                "Please install it from https://cli.github.com/",
                user_message=(
                    "GitHub CLI is not available. Install it from "
                    "https://cli.github.com/ and run `gh auth login`."
                ),
            ) from None

    def _run_gh_command(self, command: list[str]) -> str:
        """Run a GitHub CLI command."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RepositoryError(
                f"GitHub CLI command failed: {e.stderr}",
                user_message=(
                    "GitHub CLI command failed. Check your authentication "
                    "with `gh auth status` and try again."
                ),
            ) from e

    def create_repository(self, repo: Repository) -> str:
        """Create a new repository using GitHub CLI.

        Args:
            repo: Repository object with name, visibility, and description.

        Returns:
            The URL of the created repository.

        Raises:
            RepositoryError: If repository creation fails.
        """
        if not repo.is_valid:
            raise RepositoryError(
                "Invalid repository name",
                user_message=(
                    "Invalid repository name. Use only letters, numbers, "
                    "hyphens, and underscores."
                ),
            )

        try:
            command = [
                "gh",
                "repo",
                "create",
                repo.name,
                f"--{repo.visibility.value}",
            ]

            if repo.description:
                command.extend(["--description", repo.description])

            output = self._run_gh_command(command)
            return output

        except RepositoryError:
            raise
        except Exception as e:
            raise RepositoryError(
                f"Unexpected error creating repository: {e}",
                user_message=(
                    "Unexpected error while creating the repository. "
                    "Verify your GitHub CLI setup and try again."
                ),
            ) from e

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with GitHub CLI."""
        try:
            self._run_gh_command(["gh", "auth", "status"])
            return True
        except RepositoryError:
            return False
