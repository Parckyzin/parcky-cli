from pydantic import BaseModel, Field

from ai_cli.core.common.enums import RepositoryVisibility


class Repository(BaseModel):
    """Represents a GitHub repository to be created."""

    name: str = Field(
        ...,
        description="Name of the repository.",
    )
    visibility: RepositoryVisibility = Field(
        RepositoryVisibility.PRIVATE,
        description="Visibility of the repository (private or public).",
    )
    description: str = Field(
        "",
        description="Description of the repository.",
    )

    @property
    def is_valid(self) -> bool:
        """Check if repository name is valid."""
        return bool(self.name and self.name.strip())
