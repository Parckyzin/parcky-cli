"""
Git repository implementation.
"""

import subprocess

from ..config.settings import GitConfig
from ..core.exceptions import GitError, NoStagedChangesError
from ..core.interfaces import GitRepositoryInterface
from ..core.models import FileChange, GitBranch, GitDiff


class GitRepository(GitRepositoryInterface):
    """Git repository operations implementation."""

    def __init__(self, config: GitConfig):
        self.config = config

    def _run_command(self, command: str) -> str:
        """Run a git command and return the output."""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise GitError(f"Git command failed: {command}\nError: {e.stderr}") from e

    def get_staged_diff(self) -> GitDiff:
        """Get the diff of staged changes."""
        try:
            diff_output = self._run_command("git diff --cached")

            if not diff_output:
                raise NoStagedChangesError(
                    "No staged changes found. Use 'git add' first."
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
                "Failed to get staged diff. Make sure you're in a git repository."
            ) from None

    def get_current_branch(self) -> GitBranch:
        """Get the current branch name."""
        try:
            branch_name = self._run_command("git branch --show-current")
            if not branch_name:
                raise GitError("Could not determine current branch")
            return GitBranch(name=branch_name)
        except subprocess.CalledProcessError:
            raise GitError("Failed to get current branch") from None

    def commit(self, message: str) -> bool:
        """Create a commit with the given message."""
        try:
            # Escape quotes in the message
            escaped_message = message.replace('"', '\\"')
            self._run_command(f'git commit -m "{escaped_message}"')
            return True
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to create commit: {e.stderr}") from e

    def push(self, branch: str) -> bool:
        """Push changes to the remote repository."""
        try:
            self._run_command(f"git push origin {branch}")
            return True
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to push to branch {branch}: {e.stderr}") from e

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
            # Get modified/staged/deleted files
            status_output = self._run_command("git status --porcelain")
            if not status_output:
                return []

            changes = []
            for line in status_output.split("\n"):
                if not line.strip():
                    continue
                # Format: XY filename (X=staged status, Y=unstaged status)
                status = line[:2].strip()
                file_path = line[3:].strip()

                # Handle renamed files (R status shows "old -> new")
                if " -> " in file_path:
                    file_path = file_path.split(" -> ")[1]

                # Skip if status is empty
                if status:
                    changes.append(FileChange(path=file_path, status=status))

            return changes
        except subprocess.CalledProcessError:
            raise GitError("Failed to get changed files") from None

    def stage_files(self, file_paths: list[str]) -> bool:
        """Stage specific files."""
        if not file_paths:
            return True
        try:
            # Quote file paths to handle spaces
            quoted_paths = " ".join(f'"{path}"' for path in file_paths)
            self._run_command(f"git add {quoted_paths}")
            return True
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to stage files: {e.stderr}") from e

    def get_diff_for_files(self, file_paths: list[str]) -> GitDiff:
        """Get diff for specific files (works for both staged and unstaged)."""
        if not file_paths:
            return GitDiff(content="", is_truncated=False)
        try:
            quoted_paths = " ".join(f'"{path}"' for path in file_paths)
            # Get diff for the files (combine staged and unstaged)
            diff_output = self._run_command(f"git diff HEAD -- {quoted_paths}")

            # If no diff against HEAD, try without HEAD (for new files)
            if not diff_output:
                diff_output = self._run_command(f"git diff --cached -- {quoted_paths}")

            # For untracked files, we need to show file contents
            if not diff_output:
                # Check if files are untracked
                for path in file_paths:
                    try:
                        content = self._run_command(f"cat '{path}'")
                        if content:
                            diff_output += f"\n+++ new file: {path}\n{content}\n"
                    except subprocess.CalledProcessError:
                        pass

            is_truncated = False
            if len(diff_output) > self.config.max_diff_size:
                diff_output = (
                    diff_output[: self.config.max_diff_size] + "\n...[TRUNCATED]"
                )
                is_truncated = True

            return GitDiff(content=diff_output, is_truncated=is_truncated)
        except subprocess.CalledProcessError:
            raise GitError("Failed to get diff for files") from None

    def unstage_all(self) -> bool:
        """Unstage all staged files."""
        try:
            self._run_command("git reset HEAD")
            return True
        except subprocess.CalledProcessError:
            # If nothing is staged, reset might fail - that's ok
            return True

    def get_default_branch(self) -> str:
        """Get the default branch name (main or master)."""
        try:
            # Try to get from remote
            result = self._run_command(
                "git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null || echo ''"
            )
            if result:
                return result.split("/")[-1]

            # Fallback: check if main or master exists
            branches = self._run_command("git branch -a")
            if "main" in branches:
                return "main"
            return "master"
        except subprocess.CalledProcessError:
            return "main"

    def get_branch_commits(self, base_branch: str | None = None) -> list[str]:
        """Get commit messages for the current branch since branching from base."""
        try:
            if base_branch is None:
                base_branch = self.get_default_branch()

            # Get commits on current branch not in base branch
            commits_output = self._run_command(
                f"git log {base_branch}..HEAD --pretty=format:'%s' 2>/dev/null || echo ''"
            )

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

            diff_output = self._run_command(f"git diff {base_branch}...HEAD")

            if not diff_output:
                # Try alternative diff approach
                diff_output = self._run_command(f"git diff {base_branch}..HEAD")

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
                "Make sure you're not on the default branch."
            ) from None

    def get_branch_files_changed(self, base_branch: str | None = None) -> list[str]:
        """Get list of files changed in current branch compared to base."""
        try:
            if base_branch is None:
                base_branch = self.get_default_branch()

            files_output = self._run_command(
                f"git diff {base_branch}...HEAD --name-only"
            )

            if not files_output:
                return []

            return [f.strip() for f in files_output.split("\n") if f.strip()]
        except subprocess.CalledProcessError:
            return []

