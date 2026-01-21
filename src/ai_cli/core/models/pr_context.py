from dataclasses import dataclass


@dataclass(frozen=True)
class PRFileChange:
    """File change with status and optional metadata."""

    path: str
    status: str
    old_path: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class PRFileStat:
    """Diff stats for a single file."""

    path: str
    insertions: int
    deletions: int

    @property
    def churn(self) -> int:
        """Total changes for the file."""
        return self.insertions + self.deletions


@dataclass(frozen=True)
class PRDiffStats:
    """Aggregate diff stats."""

    files: list[PRFileStat]
    total_files: int
    total_insertions: int
    total_deletions: int


@dataclass(frozen=True)
class PRPatchExcerpt:
    """Excerpted patch for a file."""

    path: str
    excerpt: str
    reason: str | None = None


@dataclass(frozen=True)
class PRContext:
    """Context payload for AI-generated pull requests."""

    base_branch: str
    current_branch: str
    commits: list[str]
    commit_summary: str
    files_changed: list[PRFileChange]
    diff_stats: PRDiffStats
    patch_excerpt: list[PRPatchExcerpt]
    is_truncated: bool
    excluded_files: list[str]
    truncation_notes: list[str]
