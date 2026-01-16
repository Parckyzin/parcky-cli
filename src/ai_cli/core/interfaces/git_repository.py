from abc import ABC, abstractmethod

from ai_cli.core.models import FileChange, GitBranch, GitDiff


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
