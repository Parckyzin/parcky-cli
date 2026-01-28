from abc import ABC, abstractmethod

from ai_cli.core.models import PullRequest


class PullRequestServiceInterface(ABC):
    """Interface for pull request operations."""

    @abstractmethod
    def create_pull_request(self, pr: PullRequest) -> bool:
        """Create a pull request."""
        pass
