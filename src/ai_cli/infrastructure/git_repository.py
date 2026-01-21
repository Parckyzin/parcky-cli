"""
Git repository implementation.
"""

import os
import re
import subprocess
from collections.abc import Iterable

from ..config.settings import GitConfig
from ..core.exceptions import GitError, NoStagedChangesError
from ..core.interfaces import GitRepositoryInterface
from ..core.models import FileChange, GitBranch, GitDiff


class GitRepository(GitRepositoryInterface):
    """Git repository operations implementation."""

    def __init__(self, config: GitConfig):
        self.config = config
        # Use AI_CLI_WORK_DIR if set, otherwise use current directory
        self.work_dir = os.environ.get("AI_CLI_WORK_DIR", os.getcwd())

    def _run_command(self, command: list[str]) -> str:
        """Run a git command and return the output.

        Security: use argument lists (shell=False) to avoid shell injection.
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.work_dir,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            cmd_display = " ".join(command)
            raise GitError(
                f"Git command failed: {cmd_display}\nError: {e.stderr}",
                user_message=(
                    "Git command failed. Make sure git is installed and you are "
                    "inside a git repository."
                ),
            ) from e

    def get_staged_diff(self) -> GitDiff:
        """Get the diff of staged changes."""
        try:
            diff_output = self._run_command(["git", "diff", "--cached"])

            if not diff_output:
                raise NoStagedChangesError(
                    "No staged changes found. Use 'git add' first.",
                    user_message=(
                        "No staged changes found. Stage your files with "
                        "`git add` and try again."
                    ),
                )

            is_truncated = False
            if len(diff_output) > self.config.max_diff_size:
                diff_output = (
                    diff_output[: self.config.max_diff_size] + "\n...[TRUNCATED]"
                )
                is_truncated = True

            return GitDiff(content=diff_output, is_truncated=is_truncated)

        except subprocess.CalledProcessError:
            raise GitError(
                "Failed to get staged diff. Make sure you're in a git repository.",
                user_message=(
                    "Unable to read staged changes. Ensure you are in a git "
                    "repository and try again."
                ),
            ) from None

    def get_current_branch(self) -> GitBranch:
        """Get the current branch name."""
        try:
            branch_name = self._run_command(["git", "branch", "--show-current"])
            if not branch_name:
                raise GitError(
                    "Could not determine current branch",
                    user_message=(
                        "Unable to determine the current branch. Check your git "
                        "repository state."
                    ),
                )
            return GitBranch(name=branch_name)
        except subprocess.CalledProcessError:
            raise GitError(
                "Failed to get current branch",
                user_message=(
                    "Unable to determine the current branch. Check that the "
                    "repository is valid."
                ),
            ) from None

    def commit(self, message: str) -> bool:
        """Create a commit with the given message."""
        try:
            self._run_command(["git", "commit", "-m", message])
            return True
        except subprocess.CalledProcessError as e:
            raise GitError(
                f"Failed to create commit: {e.stderr}",
                user_message=(
                    "Commit failed. Check your git status and ensure you have "
                    "staged changes."
                ),
            ) from e

    def push(self, branch: str) -> bool:
        """Push changes to the remote repository."""
        try:
            self._run_command(["git", "push", "origin", branch])
            return True
        except subprocess.CalledProcessError as e:
            raise GitError(
                f"Failed to push to branch {branch}: {e.stderr}",
                user_message=(
                    "Push failed. Check your network connection and remote "
                    "permissions, then try again."
                ),
            ) from e

    def has_staged_changes(self) -> bool:
        """Check if there are any staged changes."""
        try:
            diff = self.get_staged_diff()
            return not diff.is_empty
        except NoStagedChangesError:
            return False

    def get_all_changes(self) -> list[FileChange]:
        """Get all changed files (staged and unstaged, including untracked)."""
        try:
            status_output = self._run_command(["git", "status", "--porcelain"])
            if not status_output:
                return []

            changes = []
            for line in status_output.split("\n"):
                if not line.strip():
                    continue
                status_regex = r"^([ MADRCU\?]{1,2})\s+(.+)$"
                match = re.match(status_regex, line)
                if not match:
                    continue
                status = match.group(1).strip()
                file_path = match.group(2).strip()

                if " -> " in file_path:
                    file_path = file_path.split(" -> ")[1]

                if status:
                    changes.append(FileChange(path=file_path, status=status))

            return changes
        except subprocess.CalledProcessError:
            raise GitError(
                "Failed to get changed files",
                user_message=(
                    "Unable to read repository status. Ensure this is a git "
                    "repository."
                ),
            ) from None

    def stage_files(self, file_paths: list[str]) -> bool:
        """Stage specific files."""
        if not file_paths:
            return True
        try:
            self._run_command(["git", "add", *file_paths])
            return True
        except subprocess.CalledProcessError as e:
            raise GitError(
                f"Failed to stage files: {e.stderr}",
                user_message=(
                    "Staging failed. Check that the file paths exist and try again."
                ),
            ) from e

    def get_diff_for_files(self, file_paths: list[str]) -> GitDiff:
        """Get diff for specific files (works for both staged and unstaged)."""
        if not file_paths:
            return GitDiff(content="", is_truncated=False)
        try:
            diff_output = self._run_command(["git", "diff", "HEAD", "--", *file_paths])

            if not diff_output:
                diff_output = self._run_command(
                    ["git", "diff", "--cached", "--", *file_paths]
                )

            if not diff_output:
                for path in file_paths:
                    try:
                        abs_path = os.path.join(self.work_dir, path)
                        content = ""
                        with open(abs_path, encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        if content:
                            diff_output += f"\n+++ new file: {path}\n{content}\n"
                    except subprocess.CalledProcessError:
                        pass
                    except OSError:
                        pass

            is_truncated = False
            if len(diff_output) > self.config.max_diff_size:
                diff_output = (
                    diff_output[: self.config.max_diff_size] + "\n...[TRUNCATED]"
                )
                is_truncated = True

            return GitDiff(content=diff_output, is_truncated=is_truncated)
        except subprocess.CalledProcessError:
            raise GitError(
                "Failed to get diff for files",
                user_message="Unable to compute diff for the selected files.",
            ) from None

    def get_staged_file_paths(self) -> list[str]:
        """Get list of staged file paths."""
        try:
            output = self._run_command(["git", "diff", "--cached", "--name-only"])
            if not output:
                return []
            return [line.strip() for line in output.split("\n") if line.strip()]
        except subprocess.CalledProcessError:
            raise GitError(
                "Failed to get staged files",
                user_message="Unable to list staged files. Check your repository.",
            ) from None

    def build_ai_context(
        self,
        diff: GitDiff,
        max_files: int = 20,
        max_example_lines: int = 120,
    ) -> str:
        """Build a structured, size-limited context for AI."""
        files = self._extract_files_from_diff(diff.content)
        summary_lines = [
            "SUMMARY",
            f"Files changed: {len(files)}",
        ]
        for file_path in files[:max_files]:
            summary_lines.append(f"- {file_path}")
        if len(files) > max_files:
            summary_lines.append(f"... and {len(files) - max_files} more")

        example_lines = diff.content.splitlines()[:max_example_lines]
        examples = "\n".join(example_lines) if example_lines else "No diff available."

        context_parts = [
            "\n".join(summary_lines),
            "EXAMPLES",
            examples,
        ]

        if diff.is_truncated:
            context_parts.append("NOTE: Original diff was truncated.")

        return "\n\n".join(context_parts)

    def unstage_all(self) -> bool:
        """Unstage all staged files."""
        try:
            self._run_command(["git", "reset", "HEAD"])
            return True
        except subprocess.CalledProcessError:
            return True

    def _extract_files_from_diff(self, diff_content: str) -> list[str]:
        """Extract file paths from a unified diff."""
        files: list[str] = []
        for line in diff_content.splitlines():
            if line.startswith("diff --git"):
                parts = line.split()
                if len(parts) >= 4:
                    candidate = parts[2]
                    if candidate.startswith("a/"):
                        candidate = candidate[2:]
                    files.append(candidate)
        return sorted(self._dedupe(files))

    def _dedupe(self, items: Iterable[str]) -> list[str]:
        """Deduplicate while preserving order."""
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    def get_default_branch(self) -> str:
        """Get the default branch name (main or master)."""
        try:
            try:
                result = self._run_command(
                    ["git", "symbolic-ref", "refs/remotes/origin/HEAD"]
                )
                if result:
                    return result.split("/")[-1]
            except subprocess.CalledProcessError:
                pass

            try:
                remote_branches = self._run_command(["git", "branch", "-r"])
                if "origin/main" in remote_branches:
                    return "main"
                if "origin/master" in remote_branches:
                    return "master"
            except subprocess.CalledProcessError:
                pass

            try:
                local_branches = self._run_command(["git", "branch"])
                for line in local_branches.split("\n"):
                    branch = line.strip().lstrip("* ")
                    if branch == "main":
                        return "main"
                    if branch == "master":
                        return "master"
            except subprocess.CalledProcessError:
                pass

            return "main"
        except Exception:
            return "main"

    def get_branch_commits(self, base_branch: str | None = None) -> list[str]:
        """Get commit messages for the current branch since branching from base."""
        try:
            if base_branch is None:
                base_branch = self.get_default_branch()

            # Avoid shell redirection; git will error if range is invalid.
            commits_output = ""
            try:
                commits_output = self._run_command(
                    ["git", "log", f"{base_branch}..HEAD", "--pretty=format:%s"]
                )
            except GitError:
                commits_output = ""

            if not commits_output:
                return []

            return [c.strip() for c in commits_output.split("\n") if c.strip()]
        except subprocess.CalledProcessError:
            return []

    def get_branch_diff(self, base_branch: str | None = None) -> GitDiff:
        """Get the diff between current branch and base branch."""
        try:
            if base_branch is None:
                base_branch = self.get_default_branch()

            diff_output = self._run_command(["git", "diff", f"{base_branch}...HEAD"])

            if not diff_output:
                diff_output = self._run_command(["git", "diff", f"{base_branch}..HEAD"])

            is_truncated = False
            if len(diff_output) > self.config.max_diff_size:
                diff_output = (
                    diff_output[: self.config.max_diff_size] + "\n...[TRUNCATED]"
                )
                is_truncated = True

            return GitDiff(content=diff_output, is_truncated=is_truncated)
        except subprocess.CalledProcessError:
            raise GitError(
                f"Failed to get diff against {base_branch}. "
                "Make sure you're not on the default branch.",
                user_message=(
                    "Unable to compare branches. Make sure you are not on the "
                    "default branch and try again."
                ),
            ) from None

    def get_branch_files_changed(self, base_branch: str | None = None) -> list[str]:
        """Get list of files changed in current branch compared to base."""
        try:
            if base_branch is None:
                base_branch = self.get_default_branch()

            files_output = self._run_command(
                ["git", "diff", f"{base_branch}...HEAD", "--name-only"]
            )

            if not files_output:
                return []

            return [f.strip() for f in files_output.split("\n") if f.strip()]
        except subprocess.CalledProcessError:
            return []
