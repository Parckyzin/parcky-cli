from pydantic import BaseModel, Field


class GitDiff(BaseModel):
    """Represents git diff information."""

    content: str = Field(..., description="The git diff content as a string.")
    is_truncated: bool = Field(
        False, description="Indicates if the diff content is truncated."
    )
    truncation_notes: list[str] = Field(
        default_factory=list,
        description="Notes explaining why or how the diff/context was truncated.",
    )

    @property
    def is_empty(self) -> bool:
        """Check if diff is empty."""
        return not self.content.strip()
