"""
Service for smart commit all operations - commits all changes grouped by folder/context.
"""

from collections import defaultdict
from dataclasses import dataclass

from ..config.prompts import get_prompt
from ..core.interfaces import AIServiceInterface, GitRepositoryInterface
from ..core.models import FileChange, FileGroup


@dataclass
class CommitResult:
    """Result of a single commit operation."""

    folder: str
    files: list[str]
    commit_message: str
    success: bool
    error: str | None = None


@dataclass
class SmartCommitAllResult:
    """Result of the smart commit all operation."""

    total_files: int
    total_commits: int
    successful_commits: int
    failed_commits: int
    commits: list[CommitResult]
    pushed: bool = False


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

    def group_files_by_folder(
        self, changes: list[FileChange]
    ) -> dict[str, list[FileChange]]:
        """Group changed files by their folder."""
        groups: dict[str, list[FileChange]] = defaultdict(list)
        for change in changes:
            groups[change.folder].append(change)
        return dict(groups)

    def analyze_file_correlation(
        self, files: list[FileChange], folder: str
    ) -> list[FileGroup]:
        """
        Analyze files in a folder and group correlated files together.
        Uses AI to determine which files should be committed together.
        """
        if len(files) <= 1:
            return [FileGroup(files=files, folder=folder)]

        file_paths = [f.path for f in files]
        diff = self.git_repo.get_diff_for_files(file_paths)

        # Get prompt template and fill in variables
        prompt_template = get_prompt("file_correlation")
        files_list = "\n".join(f"- {f.path} ({f.status})" for f in files)
        diff_content = diff.content[:3000] if diff.content else "No diff available"

        prompt = prompt_template.format(
            folder=folder,
            files_list=files_list,
            diff_content=diff_content,
        )

        try:
            response = self.ai_service._generate_content(prompt, "")
            groups = self._parse_group_response(response, files, folder)
            return groups
        except Exception:
            # If AI fails, fall back to single group
            return [FileGroup(files=files, folder=folder)]

    def _parse_group_response(
        self, response: str, files: list[FileChange], folder: str
    ) -> list[FileGroup]:
        """Parse AI response to extract file groups."""
        groups: list[FileGroup] = []
        file_map = {f.path: f for f in files}
        file_basenames = {f.filename: f for f in files}
        assigned_files: set[str] = set()

        for line in response.split("\n"):
            line = line.strip()
            if not line.upper().startswith("GROUP:"):
                continue

            group_files_str = line[6:].strip()
            group_file_names = [
                name.strip() for name in group_files_str.split(",") if name.strip()
            ]

            group_files: list[FileChange] = []
            for name in group_file_names:
                # Try to match by full path first, then by basename
                if name in file_map and name not in assigned_files:
                    group_files.append(file_map[name])
                    assigned_files.add(name)
                elif name in file_basenames:
                    full_path = file_basenames[name].path
                    if full_path not in assigned_files:
                        group_files.append(file_basenames[name])
                        assigned_files.add(full_path)

            if group_files:
                groups.append(FileGroup(files=group_files, folder=folder))

        # Add any unassigned files as individual groups
        for file in files:
            if file.path not in assigned_files:
                groups.append(FileGroup(files=[file], folder=folder))

        return groups if groups else [FileGroup(files=files, folder=folder)]

    def generate_commit_message_for_group(self, group: FileGroup) -> str:
        """Generate a commit message for a file group."""
        diff = self.git_repo.get_diff_for_files(group.file_paths)
        group.diff = diff
        commit_message = self.ai_service.generate_commit_message(diff)
        group.commit_message = commit_message
        return commit_message

    def commit_group(self, group: FileGroup) -> CommitResult:
        """Stage and commit a file group."""
        try:
            # Stage the files
            self.git_repo.stage_files(group.file_paths)

            # Generate commit message if not already done
            if not group.commit_message:
                self.generate_commit_message_for_group(group)

            # Create the commit
            self.git_repo.commit(group.commit_message)

            return CommitResult(
                folder=group.folder,
                files=group.file_paths,
                commit_message=group.commit_message,
                success=True,
            )
        except Exception as e:
            return CommitResult(
                folder=group.folder,
                files=group.file_paths,
                commit_message=group.commit_message or "",
                success=False,
                error=str(e),
            )

    def execute_smart_commit_all(self, auto_push: bool = True) -> SmartCommitAllResult:
        """
        Execute the smart commit all workflow.

        1. Get all changed files
        2. Group files by folder
        3. For each folder, analyze correlation and create sub-groups
        4. Generate commit messages for each group
        5. Create commits for each group
        6. Optionally push all changes
        """
        # Get all changes
        changes = self.get_all_changes()
        if not changes:
            return SmartCommitAllResult(
                total_files=0,
                total_commits=0,
                successful_commits=0,
                failed_commits=0,
                commits=[],
            )

        self.git_repo.unstage_all()

        folder_groups = self.group_files_by_folder(changes)

        all_groups: list[FileGroup] = []
        for folder, files in folder_groups.items():
            correlated_groups = self.analyze_file_correlation(files, folder)
            all_groups.extend(correlated_groups)

        # Commit each group
        commit_results: list[CommitResult] = []
        for group in all_groups:
            result = self.commit_group(group)
            commit_results.append(result)

        # Calculate stats
        successful = sum(1 for r in commit_results if r.success)
        failed = sum(1 for r in commit_results if not r.success)

        # Push if requested and there were successful commits
        pushed = False
        if auto_push and successful > 0:
            try:
                branch = self.git_repo.get_current_branch()
                self.git_repo.push(branch.name)
                pushed = True
            except Exception:
                pushed = False

        return SmartCommitAllResult(
            total_files=len(changes),
            total_commits=len(commit_results),
            successful_commits=successful,
            failed_commits=failed,
            commits=commit_results,
            pushed=pushed,
        )
