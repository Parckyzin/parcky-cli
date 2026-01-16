from abc import ABC, abstractmethod

from ai_cli.core.models import GitDiff, PullRequest


class AIServiceInterface(ABC):
    """Interface for AI service operations."""

    @abstractmethod
    def generate_commit_message(self, diff: GitDiff) -> str:
        """Generate a commit message based on the diff."""
        pass

    @abstractmethod
    def generate_pull_request(self, diff: GitDiff, commit_msg: str) -> PullRequest:
        """Generate a pull request title and description."""
        pass
