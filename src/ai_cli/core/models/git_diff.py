from pydantic import Field, BaseModel


class GitDiff(BaseModel):
    """Represents git diff information."""

    content: str = Field(..., description="The git diff content as a string.")
    is_truncated: bool = Field(
        False, description="Indicates if the diff content is truncated."
    )

    @property
    def is_empty(self) -> bool:
        """Check if diff is empty."""
        return not self.content.strip()

