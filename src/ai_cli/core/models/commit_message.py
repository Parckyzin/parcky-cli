from typing import Optional

from pydantic import BaseModel, Field

from ai_cli.core.common.enums import CommitType


class CommitMessage(BaseModel):
    """Represents a commit message following Conventional Commits."""

    type: CommitType = Field(..., description="Type of the commit.")
    scope: Optional[str] = Field(None, description="Scope of the commit (optional).")
    subject: str = Field(..., description="Short description of the commit.")
    body: Optional[str] = Field(None, description="Detailed description of the commit.")
    footer: Optional[str] = Field(
        None, description="Footer information (e.g., breaking changes, issues)."
    )

    def __str__(self) -> str:
        """Format commit message."""
        scope_part = f"({self.scope})" if self.scope else ""
        return f"{self.type}{scope_part}: {self.subject}"

    @property
    def full_message(self) -> str:
        """Get full commit message including body and footer."""
        msg = str(self)
        if self.body:
            msg += f"\n\n{self.body}"
        if self.footer:
            msg += f"\n\n{self.footer}"
        return msg
