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

    @abstractmethod
    def generate_text(self, prompt: str, context: str) -> str:
        """Generate a raw text response from a prompt and context."""
        pass

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Get a list of available AI models from the service."""
        pass
