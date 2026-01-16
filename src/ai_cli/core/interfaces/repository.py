from abc import ABC, abstractmethod

from ai_cli.core.models import Repository


class RepositoryServiceInterface(ABC):
    """Interface for repository operations."""

    @abstractmethod
    def create_repository(self, repo: Repository) -> str:
        """Create a new repository. Returns the repository URL."""
        pass
