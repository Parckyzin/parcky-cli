from pydantic import BaseModel, Field
from typing import Optional

from ai_cli.core.models.file_change import FileChange
from ai_cli.core.models.git_diff import GitDiff


class FileGroup(BaseModel):
    """Represents a group of related files to be committed together."""

    files: list[FileChange] = Field(
        ..., description="List of files in this group."
    )
    folder: str = Field(
        ..., description="Common folder containing these files."
    )
    diff: Optional[GitDiff] = Field(
        None, description="Git diff for the files in this group."
    )
    commit_message: Optional[str] = Field(
        None, description="Generated commit message for this file group."
    )

    @property
    def file_paths(self) -> list[str]:
        """Get list of file paths in this group."""
        return [f.path for f in self.files]

    @property
    def file_count(self) -> int:
        """Get number of files in this group."""
        return len(self.files)
