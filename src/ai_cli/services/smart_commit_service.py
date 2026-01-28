"""
Main service orchestrating the smart commit workflow.
"""

from typing import Optional

from ai_cli.pipelines import commit_message as commit_message_pipeline

from ..core.exceptions import AIServiceError
from ..core.interfaces import (
    AIServiceInterface,
    GitRepositoryInterface,
    PullRequestServiceInterface,
)
from ..core.models import GitDiff


class SmartCommitService:
    """Service for smart commit operations."""

    def __init__(
        self,
        git_repo: GitRepositoryInterface,
        ai_service: AIServiceInterface,
        pr_service: Optional[PullRequestServiceInterface] = None,
    ):
        self.git_repo = git_repo
        self.ai_service = ai_service
        self.pr_service = pr_service

    def get_staged_changes(self) -> GitDiff:
        """Get staged changes from git repository."""
        return self.git_repo.get_staged_diff()

    def generate_commit_message(self, diff: GitDiff) -> str:
        """Generate AI-powered commit message."""
        try:
            staged_files = self.git_repo.get_staged_file_paths()
        except Exception:
            staged_files = []
        ai_context = commit_message_pipeline.build_commit_context(diff, staged_files)
        ai_diff = GitDiff(
            content=ai_context,
            is_truncated=diff.is_truncated,
            truncation_notes=diff.truncation_notes,
        )
        try:
            return self.ai_service.generate_commit_message(ai_diff)
        except AIServiceError:
            return self._fallback_commit_message()

    def _fallback_commit_message(self) -> str:
        """Create a deterministic fallback commit message."""
        try:
            files = self.git_repo.get_staged_file_paths()
        except Exception:
            return "chore: update files"
        if not files:
            return "chore: update files"
        if len(files) == 1:
            filename = files[0].split("/")[-1]
            return f"chore: update {filename}"
        return f"chore: update {len(files)} files"

    def create_commit(self, message: str) -> bool:
        """Create git commit with the provided message."""
        return self.git_repo.commit(message)

    def push_changes(self, auto_push: bool = True) -> bool:
        """Push changes to remote repository."""
        if not auto_push:
            return True

        current_branch = self.git_repo.get_current_branch()
        return self.git_repo.push(current_branch.name)

    def create_pull_request(self, diff: GitDiff, commit_msg: str) -> bool:
        """Create a pull request."""
        if not self.pr_service:
            raise ValueError("PR service not configured")

        pr = self.ai_service.generate_pull_request(diff, commit_msg)
        return self.pr_service.create_pull_request(pr)

    def execute_smart_commit(
        self, auto_push: bool = True, create_pr: bool = False
    ) -> dict:
        """Execute the complete smart commit workflow."""
        results = {
            "diff_retrieved": False,
            "commit_created": False,
            "pushed": False,
            "pr_created": False,
            "diff": None,
            "commit_message": None,
            "branch": None,
            "errors": [],
        }

        try:
            diff = self.get_staged_changes()
            results["diff_retrieved"] = True
            results["diff"] = diff

            commit_msg = self.generate_commit_message(diff)
            results["commit_message"] = commit_msg

            results["commit_created"] = self.create_commit(commit_msg)

            current_branch = self.git_repo.get_current_branch()
            results["branch"] = current_branch.name

            if auto_push:
                results["pushed"] = self.push_changes(auto_push)

            if create_pr:
                results["pr_created"] = self.create_pull_request(diff, commit_msg)

        except Exception as e:
            results["errors"].append(str(e))

        return results
