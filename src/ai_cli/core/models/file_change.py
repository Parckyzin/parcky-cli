from pydantic import BaseModel, Field


class FileChange(BaseModel):
    """Represents a changed file in the repository."""

    path: str = Field(..., description="Path to the changed file.")
    status: str = Field(..., description="Status of the file change (e.g., M, A, D).")

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
