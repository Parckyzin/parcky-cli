"""
Pull request service implementation using GitHub CLI.
"""

import os
import subprocess

from ..core.exceptions import PullRequestError
from ..core.interfaces import PullRequestServiceInterface
from ..core.models import PullRequest


class GitHubPRService(PullRequestServiceInterface):
    """GitHub pull request service using GitHub CLI."""

    def __init__(self, work_dir: str | None = None):
        # Ensure gh is available
        self._check_gh_cli()
        # Align working directory with git operations (matches GitRepository)
        self.work_dir = work_dir or os.environ.get("AI_CLI_WORK_DIR", os.getcwd())

    def _check_gh_cli(self) -> None:
        """Check if GitHub CLI is available."""
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise PullRequestError(
                "GitHub CLI (gh) is not installed or not available. "
                "Please install it from https://cli.github.com/",
                user_message=(
                    "GitHub CLI is not available. Install it from "
                    "https://cli.github.com/ and run `gh auth login`."
                ),
            ) from None

    def _run_gh_command(self, command: list) -> str:
        """Run a GitHub CLI command in the target repository directory."""
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=True, cwd=self.work_dir
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise PullRequestError(
                f"GitHub CLI command failed: {e.stderr}",
                user_message=(
                    "GitHub CLI command failed. Check your authentication "
                    "with `gh auth status` and try again."
                ),
            ) from e

    def create_pull_request(self, pr: PullRequest) -> bool:
        """Create a pull request using GitHub CLI."""
        try:
            command = [
                "gh",
                "pr",
                "create",
                "--title",
                pr.title,
                "--body",
                pr.body,
                "--web",
            ]

            self._run_gh_command(command)
            return True

        except PullRequestError:
            raise
        except Exception as e:
            raise PullRequestError(
                f"Unexpected error creating pull request: {e}",
                user_message=(
                    "Unexpected error while creating the pull request. "
                    "Verify your GitHub CLI setup and try again."
                ),
            ) from e

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with GitHub CLI."""
        try:
            self._run_gh_command(["gh", "auth", "status"])
            return True
        except PullRequestError:
            return False

    def get_repository_info(self) -> dict:
        """Get current repository information."""
        try:
            output = self._run_gh_command(
                ["gh", "repo", "view", "--json", "name,owner"]
            )
            import json

            return json.loads(output)
        except Exception as e:
            raise PullRequestError(
                f"Failed to get repository info: {e}",
                user_message=(
                    "Failed to read repository info from GitHub CLI. "
                    "Check `gh auth status`."
                ),
            ) from e
