from pydantic import BaseModel, Field

from ai_cli.core.models.file_change import FileChange
from ai_cli.core.models.git_diff import GitDiff


class FileGroup(BaseModel):
    """Represents a group of related files to be committed together."""

    files: list[FileChange] = Field(..., description="List of files in this group.")
    folder: str = Field(..., description="Common folder containing these files.")
    diff: GitDiff | None = Field(
        None, description="Git diff for the files in this group."
    )
    commit_message: str | None = Field(
        None, description="Generated commit message for this file group."
    )
    explanation: str | None = Field(
        None, description="Short explanation of why these files were grouped."
    )

    @property
    def file_paths(self) -> list[str]:
        """Get list of file paths in this group."""
        return [f.path for f in self.files]

    @property
    def file_count(self) -> int:
        """Get number of files in this group."""
        return len(self.files)

    @property
    def group_key(self) -> tuple[str, str]:
        """Deterministic key for sorting groups."""
        return (self.folder, ",".join(self.file_paths))


class CommitResult(BaseModel):
    """Result of a single commit operation."""

    group: FileGroup = Field(..., description="Associated file group.")
    commit_message: str = Field(..., description="Commit message for this group.")
    status: str = Field(..., description="Commit status: planned, success, or failed.")
    error: str | None = Field(None, description="Error message when failed.")


class SmartCommitAllResult(BaseModel):
    """Result of the smart commit all operation."""

    changes: list[FileChange] = Field(
        default_factory=list, description="All detected file changes."
    )
    groups: list[FileGroup] = Field(
        default_factory=list, description="Grouped file sets."
    )
    commit_results: list[CommitResult] = Field(
        default_factory=list, description="Commit results per group."
    )
    pushed: bool = Field(False, description="Whether a push was performed.")
    dry_run: bool = Field(False, description="Whether this run was a dry-run.")

    @property
    def total_files(self) -> int:
        """Total number of files detected."""
        return len(self.changes)

    @property
    def total_groups(self) -> int:
        """Total number of groups produced."""
        return len(self.groups)

    @property
    def successful_commits(self) -> int:
        """Number of successful commits."""
        return sum(1 for r in self.commit_results if r.status == "success")

    @property
    def failed_commits(self) -> int:
        """Number of failed commits."""
        return sum(1 for r in self.commit_results if r.status == "failed")
