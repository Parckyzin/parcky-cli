"""
Service for smart commit all operations - commits all changes grouped by folder/context.
"""

from collections import defaultdict

from ai_cli.config.prompts import get_prompt
from ai_cli.core.interfaces import AIServiceInterface, GitRepositoryInterface
from ai_cli.core.models import (
    CommitResult,
    FileChange,
    FileGroup,
    GitDiff,
    SmartCommitAllResult,
)
from ai_cli.pipelines import commit_message as commit_message_pipeline
from ai_cli.pipelines import file_correlation as file_correlation_pipeline


class SmartCommitAllService:
    """Service for committing all changes grouped by folder and context."""

    def __init__(
        self,
        git_repo: GitRepositoryInterface,
        ai_service: AIServiceInterface,
    ):
        self.git_repo = git_repo
        self.ai_service = ai_service

    def get_all_changes(self) -> list[FileChange]:
        """Get all changed files in the repository."""
        return self.git_repo.get_all_changes()

    def _sort_changes(self, changes: list[FileChange]) -> list[FileChange]:
        """Sort file changes deterministically."""
        return sorted(changes, key=lambda change: (change.folder, change.path))

    def _sort_groups(self, groups: list[FileGroup]) -> list[FileGroup]:
        """Sort groups deterministically."""
        return sorted(groups, key=lambda group: group.group_key)

    def group_files_by_folder(
        self, changes: list[FileChange]
    ) -> dict[str, list[FileChange]]:
        """Group changed files by their folder."""
        groups: dict[str, list[FileChange]] = defaultdict(list)
        for change in self._sort_changes(changes):
            groups[change.folder].append(change)
        return {folder: groups[folder] for folder in sorted(groups)}

    def analyze_file_correlation(
        self, files: list[FileChange], folder: str
    ) -> list[FileGroup]:
        """
        Analyze files in a folder and group correlated files together.
        Uses AI to determine which files should be committed together.
        """
        if len(files) <= 1:
            return [
                FileGroup(
                    files=self._sort_changes(files),
                    folder=folder,
                    explanation="Single file change.",
                )
            ]

        ordered_files = self._sort_changes(files)
        file_paths = [f.path for f in ordered_files]
        diff = self.git_repo.get_diff_for_files(file_paths)

        prompt_template = get_prompt("file_correlation")
        prompt = file_correlation_pipeline.build_file_correlation_prompt(
            prompt_template,
            folder=folder,
            files=ordered_files,
            diff_content=diff.content,
        )

        try:
            response = self.ai_service.generate_text(prompt, "")
            groups = file_correlation_pipeline.parse_group_response(
                response, ordered_files, folder
            )
            return self._sort_groups(groups)
        except Exception:
            # If AI fails, fall back to single group
            return [
                FileGroup(
                    files=ordered_files,
                    folder=folder,
                    explanation="AI unavailable; grouped by folder.",
                )
            ]

    def generate_commit_message_for_group(self, group: FileGroup) -> str:
        """Generate a commit message for a file group."""
        diff = self.git_repo.get_diff_for_files(group.file_paths)
        group.diff = diff
        ai_context = commit_message_pipeline.build_commit_context(
            diff, group.file_paths
        )
        commit_message = self.ai_service.generate_commit_message(
            GitDiff(
                content=ai_context,
                is_truncated=diff.is_truncated,
                truncation_notes=diff.truncation_notes,
            )
        )
        group.commit_message = commit_message
        return commit_message

    def commit_group(self, group: FileGroup, *, dry_run: bool) -> CommitResult:
        """Stage and commit a file group."""
        try:
            if not group.commit_message:
                self.generate_commit_message_for_group(group)

            if dry_run:
                return CommitResult(
                    group=group,
                    commit_message=group.commit_message,
                    status="planned",
                )

            # Stage the files
            self.git_repo.stage_files(group.file_paths)

            # Create the commit
            self.git_repo.commit(group.commit_message)

            return CommitResult(
                group=group,
                commit_message=group.commit_message,
                status="success",
            )
        except Exception as e:
            return CommitResult(
                group=group,
                commit_message=group.commit_message or "",
                status="failed",
                error=str(e),
            )

    def plan_smart_commit_all(self) -> SmartCommitAllResult:
        """Build a deterministic plan for smart commit all."""
        changes = self.get_all_changes()
        if not changes:
            return SmartCommitAllResult()

        ordered_changes = self._sort_changes(changes)
        folder_groups = self.group_files_by_folder(ordered_changes)

        all_groups: list[FileGroup] = []
        for folder, files in folder_groups.items():
            correlated_groups = self.analyze_file_correlation(files, folder)
            all_groups.extend(correlated_groups)

        all_groups = self._sort_groups(all_groups)

        commit_results: list[CommitResult] = []
        for group in all_groups:
            commit_results.append(self.commit_group(group, dry_run=True))

        return SmartCommitAllResult(
            changes=ordered_changes,
            groups=all_groups,
            commit_results=commit_results,
            pushed=False,
            dry_run=True,
        )

    def execute_smart_commit_all(
        self,
        auto_push: bool = True,
        dry_run: bool = False,
        plan: SmartCommitAllResult | None = None,
    ) -> SmartCommitAllResult:
        """
        Execute the smart commit all workflow.

        1. Get all changed files
        2. Group files by folder
        3. For each folder, analyze correlation and create sub-groups
        4. Generate commit messages for each group
        5. Create commits for each group
        6. Optionally push all changes
        """
        plan_result = plan or self.plan_smart_commit_all()

        if dry_run or plan_result.total_files == 0:
            return plan_result

        self.git_repo.unstage_all()

        commit_results: list[CommitResult] = []
        for group in plan_result.groups:
            commit_results.append(self.commit_group(group, dry_run=False))

        pushed = False
        if auto_push and any(r.status == "success" for r in commit_results):
            try:
                branch = self.git_repo.get_current_branch()
                self.git_repo.push(branch.name)
                pushed = True
            except Exception:
                pushed = False

        return SmartCommitAllResult(
            changes=plan_result.changes,
            groups=plan_result.groups,
            commit_results=commit_results,
            pushed=pushed,
            dry_run=False,
        )
