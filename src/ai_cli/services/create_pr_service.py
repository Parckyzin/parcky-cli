"""
Service for creating pull requests based on branch changes.
"""

from dataclasses import dataclass

from ..core.exceptions import AIServiceError, GitError, PullRequestError
from ..core.interfaces import AIServiceInterface, PullRequestServiceInterface
from ..core.models import GitDiff, PRDiffStats, PRFileChange, PullRequest
from ..infrastructure.git_repository import GitRepository
from .pr_context_builder import build_pr_context


@dataclass
class BranchInfo:
    """Information about the current branch."""

    name: str
    base_branch: str
    commits: list[str]
    files_changed: list[str]
    name_status: list[PRFileChange]
    diff_stats: PRDiffStats


@dataclass
class CreatePRResult:
    """Result of PR creation."""

    success: bool
    branch_info: BranchInfo | None = None
    pr: PullRequest | None = None
    error: str | None = None


class CreatePRService:
    """Service for creating pull requests based on branch changes."""

    def __init__(
        self,
        git_repo: GitRepository,
        ai_service: AIServiceInterface,
        pr_service: PullRequestServiceInterface,
        max_context_chars: int = 35000,
    ):
        self.git_repo = git_repo
        self.ai_service = ai_service
        self.pr_service = pr_service
        self.max_context_chars = max_context_chars

    def get_branch_info(self, base_branch: str | None = None) -> BranchInfo:
        """Gather information about the current branch."""
        current_branch = self.git_repo.get_current_branch()

        if base_branch is None:
            base_branch = self.git_repo.get_default_branch()

        if current_branch.name == base_branch:
            raise GitError(
                f"You are on the default branch '{base_branch}'. "
                "Please switch to a feature branch first.",
                user_message=(
                    f"You are on the default branch '{base_branch}'. "
                    "Switch to a feature branch and try again."
                ),
            )

        commits = self.git_repo.get_branch_commits(base_branch)
        name_status = self.git_repo.get_branch_name_status(base_branch)
        files_changed = [change.path for change in name_status]
        diff_stats = self.git_repo.get_branch_diff_stats(base_branch)

        if not commits and not files_changed:
            raise GitError(
                f"No changes found between '{current_branch.name}' and '{base_branch}'. "
                "Make sure you have commits on this branch.",
                user_message=(
                    "No changes found between the current branch and base. "
                    "Commit your changes and try again."
                ),
            )

        return BranchInfo(
            name=current_branch.name,
            base_branch=base_branch,
            commits=commits,
            files_changed=files_changed,
            name_status=name_status,
            diff_stats=diff_stats,
        )

    def generate_pr_content(self, branch_info: BranchInfo) -> PullRequest:
        """Generate PR title and description using AI."""
        # Build context from branch info for commit summary
        commit_summary = "; ".join(branch_info.commits[:5])
        if len(branch_info.commits) > 5:
            commit_summary += f" (+{len(branch_info.commits) - 5} more)"

        pr_context = build_pr_context(
            git_repo=self.git_repo,
            base_branch=branch_info.base_branch,
            current_branch=branch_info.name,
            commits=branch_info.commits,
            files_changed=branch_info.name_status,
            diff_stats=branch_info.diff_stats,
            max_context_chars=self.max_context_chars,
        )
        ai_context = self.git_repo.build_ai_context(
            pr_context, max_context_chars=self.max_context_chars
        )
        ai_diff = GitDiff(
            content=ai_context,
            is_truncated=pr_context.is_truncated,
            truncation_notes=pr_context.truncation_notes,
        )
        try:
            return self.ai_service.generate_pull_request(ai_diff, commit_summary)
        except AIServiceError:
            return self._fallback_pull_request(branch_info, commit_summary)

    def _fallback_pull_request(
        self, branch_info: BranchInfo, commit_summary: str
    ) -> PullRequest:
        """Build a deterministic fallback pull request."""
        title = f"chore: update {branch_info.name}"
        commits = branch_info.commits[:10]
        files = branch_info.files_changed[:20]
        body_lines = [
            "## Summary",
            "Automated fallback PR content (AI unavailable).",
            "",
            "## Commits",
            *(f"- {commit}" for commit in commits),
        ]
        if not commits:
            body_lines.append("- No commits detected")
        body_lines.extend(
            [
                "",
                "## Files Changed",
                *(f"- {file_path}" for file_path in files),
            ]
        )
        if not files:
            body_lines.append("- No files detected")
        if commit_summary:
            body_lines.extend(["", "## Commit Summary", commit_summary])
        return PullRequest(title=title, body="\n".join(body_lines))

    def create_pr(self, base_branch: str | None = None) -> CreatePRResult:
        """
        Create a pull request for the current branch.

        Args:
            base_branch: The base branch to create PR against (default: main/master)

        Returns:
            CreatePRResult with PR details
        """
        try:
            branch_info = self.get_branch_info(base_branch)

            pr = self.generate_pr_content(branch_info)

            self.pr_service.create_pull_request(pr)

            return CreatePRResult(
                success=True,
                branch_info=branch_info,
                pr=pr,
            )

        except (GitError, PullRequestError) as e:
            return CreatePRResult(
                success=False,
                error=str(e),
            )
        except Exception as e:
            return CreatePRResult(
                success=False,
                error=f"Unexpected error: {e}",
            )
