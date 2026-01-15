"""
Service for creating pull requests based on branch changes.
"""

from dataclasses import dataclass

from ..core.exceptions import GitError, PullRequestError
from ..core.interfaces import AIServiceInterface, PullRequestServiceInterface
from ..core.models import GitDiff, PullRequest
from ..infrastructure.git_repository import GitRepository


@dataclass
class BranchInfo:
    """Information about the current branch."""

    name: str
    base_branch: str
    commits: list[str]
    files_changed: list[str]
    diff: GitDiff


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
    ):
        self.git_repo = git_repo
        self.ai_service = ai_service
        self.pr_service = pr_service

    def get_branch_info(self, base_branch: str | None = None) -> BranchInfo:
        """Gather information about the current branch."""
        current_branch = self.git_repo.get_current_branch()

        if base_branch is None:
            base_branch = self.git_repo.get_default_branch()

        # Check if we're on the default branch
        if current_branch.name == base_branch:
            raise GitError(
                f"You are on the default branch '{base_branch}'. "
                "Please switch to a feature branch first."
            )

        commits = self.git_repo.get_branch_commits(base_branch)
        files_changed = self.git_repo.get_branch_files_changed(base_branch)
        diff = self.git_repo.get_branch_diff(base_branch)

        if not commits and not files_changed:
            raise GitError(
                f"No changes found between '{current_branch.name}' and '{base_branch}'. "
                "Make sure you have commits on this branch."
            )

        return BranchInfo(
            name=current_branch.name,
            base_branch=base_branch,
            commits=commits,
            files_changed=files_changed,
            diff=diff,
        )

    def generate_pr_content(self, branch_info: BranchInfo) -> PullRequest:
        """Generate PR title and description using AI."""
        # Build context from branch info for commit summary
        commit_summary = "; ".join(branch_info.commits[:5])
        if len(branch_info.commits) > 5:
            commit_summary += f" (+{len(branch_info.commits) - 5} more)"

        return self.ai_service.generate_pull_request(branch_info.diff, commit_summary)

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
