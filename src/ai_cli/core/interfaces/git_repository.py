from abc import ABC, abstractmethod

from ai_cli.core.models import (
    FileChange,
    GitBranch,
    GitDiff,
    PRContext,
    PRDiffStats,
    PRFileChange,
)


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
    def get_staged_file_paths(self) -> list[str]:
        """Get list of staged file paths."""
        pass

    @abstractmethod
    def get_branch_name_status(
        self, base_branch: str | None = None
    ) -> list[PRFileChange]:
        """Get name-status list for branch changes."""
        pass

    @abstractmethod
    def get_branch_diff_stats(self, base_branch: str | None = None) -> PRDiffStats:
        """Get diff stats for branch changes."""
        pass

    @abstractmethod
    def get_branch_patch(self, base_branch: str, file_path: str) -> str:
        """Get diff patch for a specific file."""
        pass

    @abstractmethod
    def build_commit_context(
        self,
        diff: GitDiff,
        max_files: int = 20,
        max_example_lines: int = 120,
    ) -> str:
        """Build a structured, size-limited commit context for AI."""
        pass

    @abstractmethod
    def build_ai_context(
        self, pr_context: PRContext, max_context_chars: int = 35000
    ) -> str:
        """Build a structured, size-limited PR context for AI."""
        pass

    @abstractmethod
    def unstage_all(self) -> bool:
        """Unstage all staged files."""
        pass
