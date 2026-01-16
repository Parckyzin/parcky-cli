from pydantic import BaseModel, Field


class GitBranch(BaseModel):
    """Represents a git branch."""

    name: str = Field(..., description="Name of the git branch.")

    @property
    def is_valid(self) -> bool:
        """Check if branch name is valid."""
        return bool(self.name and self.name.strip())
