"""
Domain models for AI CLI application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RepositoryVisibility(Enum):
    """Repository visibility options."""

    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class CommitType(Enum):
    """Conventional commit types."""

    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    TEST = "test"
    CHORE = "chore"
    BUILD = "build"
    CI = "ci"
    PERF = "perf"
    REVERT = "revert"


@dataclass
class GitDiff:
    """Represents git diff information."""

    content: str
    is_truncated: bool = False

    @property
    def is_empty(self) -> bool:
        """Check if diff is empty."""
        return not self.content.strip()


@dataclass
class CommitMessage:
    """Represents a commit message following Conventional Commits."""

    type: CommitType
    scope: Optional[str]
    subject: str
    body: Optional[str] = None
    footer: Optional[str] = None

    def __str__(self) -> str:
        """Format commit message."""
        scope_part = f"({self.scope})" if self.scope else ""
        return f"{self.type.value}{scope_part}: {self.subject}"

    @property
    def full_message(self) -> str:
        """Get full commit message including body and footer."""
        msg = str(self)
        if self.body:
            msg += f"\n\n{self.body}"
        if self.footer:
            msg += f"\n\n{self.footer}"
        return msg


@dataclass
class PullRequest:
    """Represents a pull request."""

    title: str
    body: str

    @property
    def formatted_body(self) -> str:
        """Get formatted body with proper escaping."""
        return self.body.replace('"', '\\"')


@dataclass
class GitBranch:
    """Represents a git branch."""

    name: str

    @property
    def is_valid(self) -> bool:
        """Check if branch name is valid."""
        return bool(self.name and self.name.strip())


@dataclass
class Repository:
    """Represents a GitHub repository to be created."""

    name: str
    visibility: RepositoryVisibility = RepositoryVisibility.PRIVATE
    description: str = ""

    @property
    def is_valid(self) -> bool:
        """Check if repository name is valid."""
        return bool(self.name and self.name.strip())


@dataclass
class FileChange:
    """Represents a changed file in the repository."""

    path: str
    status: str  # M (modified), A (added), D (deleted), R (renamed), etc.

    @property
    def folder(self) -> str:
        """Get the folder containing this file."""
        import os

        dirname = os.path.dirname(self.path)
        return dirname if dirname else "."

    @property
    def filename(self) -> str:
        """Get just the filename."""
        import os

        return os.path.basename(self.path)


@dataclass
class FileGroup:
    """Represents a group of related files to be committed together."""

    files: list[FileChange]
    folder: str
    diff: Optional[GitDiff] = None
    commit_message: Optional[str] = None

    @property
    def file_paths(self) -> list[str]:
        """Get list of file paths in this group."""
        return [f.path for f in self.files]

    @property
    def file_count(self) -> int:
        """Get number of files in this group."""
        return len(self.files)

