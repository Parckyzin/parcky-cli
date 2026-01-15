"""
Interfaces for AI CLI application.
"""

from abc import ABC, abstractmethod

from .models import FileChange, GitBranch, GitDiff, PullRequest, Repository


class GitRepositoryInterface(ABC):
    """Interface for git repository operations."""

    @abstractmethod
    def get_staged_diff(self) -> GitDiff:
        """Get the diff of staged changes."""
        pass

    @abstractmethod
    def get_current_branch(self) -> GitBranch:
        """Get the current branch name."""
        pass

    @abstractmethod
    def commit(self, message: str) -> bool:
        """Create a commit with the given message."""
        pass

    @abstractmethod
    def push(self, branch: str) -> bool:
        """Push changes to the remote repository."""
        pass

    @abstractmethod
    def get_all_changes(self) -> list[FileChange]:
        """Get all changed files (staged and unstaged)."""
        pass

    @abstractmethod
    def stage_files(self, file_paths: list[str]) -> bool:
        """Stage specific files."""
        pass

    @abstractmethod
    def get_diff_for_files(self, file_paths: list[str]) -> GitDiff:
        """Get diff for specific files."""
        pass

    @abstractmethod
    def unstage_all(self) -> bool:
        """Unstage all staged files."""
        pass


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


class PullRequestServiceInterface(ABC):
    """Interface for pull request operations."""

    @abstractmethod
    def create_pull_request(self, pr: PullRequest) -> bool:
        """Create a pull request."""
        pass


class RepositoryServiceInterface(ABC):
    """Interface for repository operations."""

    @abstractmethod
    def create_repository(self, repo: Repository) -> str:
        """Create a new repository. Returns the repository URL."""
        pass
