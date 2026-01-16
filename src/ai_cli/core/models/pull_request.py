from pydantic import BaseModel, Field


class PullRequest(BaseModel):
    """Represents a pull request."""

    title: str = Field(..., description="Title of the pull request.")
    body: str = Field(..., description="Body/description of the pull request.")

    @property
    def formatted_body(self) -> str:
        """Get formatted body with proper escaping."""
        return self.body.replace('"', '\\"')
