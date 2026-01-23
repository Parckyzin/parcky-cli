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
from ..core.models import (
    FileChange,
    GitBranch,
    GitDiff,
    PRContext,
    PRDiffStats,
    PRFileChange,
    PRFileStat,
)


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
            truncation_notes: list[str] = []
            if len(diff_output) > self.config.max_diff_size:
                diff_output = (
                    diff_output[: self.config.max_diff_size] + "\n...[TRUNCATED]"
                )
                is_truncated = True
                truncation_notes.append(
                    "Diff truncated by GitRepository "
                    f"(max_diff_size={self.config.max_diff_size})."
                )

            return GitDiff(
                content=diff_output,
                is_truncated=is_truncated,
                truncation_notes=truncation_notes,
            )

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
                    "Unable to read repository status. Ensure this is a git repository."
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
            truncation_notes: list[str] = []
            if len(diff_output) > self.config.max_diff_size:
                diff_output = (
                    diff_output[: self.config.max_diff_size] + "\n...[TRUNCATED]"
                )
                is_truncated = True
                truncation_notes.append(
                    "Diff truncated by GitRepository "
                    f"(max_diff_size={self.config.max_diff_size})."
                )

            return GitDiff(
                content=diff_output,
                is_truncated=is_truncated,
                truncation_notes=truncation_notes,
            )
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

    def build_commit_context(
        self,
        diff: GitDiff,
        max_files: int = 20,
        max_example_lines: int = 120,
    ) -> str:
        """Compatibility proxy. Prefer pipelines.commit_message.build_commit_context."""
        from ai_cli.pipelines import commit_message as commit_message_pipeline

        file_paths = self._extract_files_from_diff(diff.content)
        return commit_message_pipeline.build_commit_context(
            diff,
            file_paths,
            max_files=max_files,
            max_example_lines=max_example_lines,
        )

    def build_ai_context(
        self, pr_context: PRContext, max_context_chars: int = 35000
    ) -> str:
        """Build a structured, size-limited PR context for AI."""
        base_sections = self._format_pr_context_sections(
            pr_context, include_patches=False
        )
        sections = base_sections[:]
        patch_section = self._format_patch_section(pr_context)
        truncation_section = self._format_truncation_section(pr_context)

        candidate_sections = sections + [patch_section]
        if truncation_section:
            candidate_sections.append(truncation_section)

        full_text = "\n\n".join(section for section in candidate_sections if section)
        if len(full_text) <= max_context_chars:
            return full_text

        # Drop patches if over budget, keep base + truncation info.
        fallback_sections = sections[:]
        truncation_notice = truncation_section or self._build_truncation_notice(
            pr_context.excluded_files, ["Patch excerpts removed to fit budget."]
        )
        if truncation_notice:
            fallback_sections.append(truncation_notice)
        return "\n\n".join(section for section in fallback_sections if section)

    def unstage_all(self) -> bool:
        """Unstage all staged files."""
        try:
            self._run_command(["git", "reset", "HEAD"])
            return True
        except subprocess.CalledProcessError:
            return True

    def get_branch_name_status(
        self, base_branch: str | None = None
    ) -> list[PRFileChange]:
        """Get name-status list for branch changes using three-dot comparison."""
        try:
            if base_branch is None:
                base_branch = self.get_default_branch()
            output = self._run_command(
                ["git", "diff", "--name-status", f"{base_branch}...HEAD"]
            )
            return self._parse_name_status(output)
        except subprocess.CalledProcessError:
            raise GitError(
                "Failed to get branch file status",
                user_message="Unable to read branch changes. Check your repository.",
            ) from None

    def get_branch_diff_stats(self, base_branch: str | None = None) -> PRDiffStats:
        """Get diff stats for branch changes using three-dot comparison."""
        try:
            if base_branch is None:
                base_branch = self.get_default_branch()
            output = self._run_command(
                ["git", "diff", "--stat", f"{base_branch}...HEAD"]
            )
            return self._parse_diff_stat_output(output)
        except subprocess.CalledProcessError:
            raise GitError(
                "Failed to get branch diff stats",
                user_message="Unable to read diff stats. Check your repository.",
            ) from None

    def get_branch_patch(self, base_branch: str, file_path: str) -> str:
        """Get diff patch for a specific file."""
        try:
            return self._run_command(
                ["git", "diff", f"{base_branch}...HEAD", "--", file_path]
            )
        except subprocess.CalledProcessError:
            raise GitError(
                f"Failed to get patch for {file_path}",
                user_message="Unable to read patch for a file in this branch.",
            ) from None

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

    def _parse_name_status(self, output: str) -> list[PRFileChange]:
        """Parse git diff --name-status output."""
        changes: list[PRFileChange] = []
        if not output:
            return changes
        for line in output.splitlines():
            parts = line.split("\t")
            if not parts:
                continue
            status = parts[0].strip()
            if status.startswith("R") and len(parts) >= 3:
                old_path = parts[1].strip()
                new_path = parts[2].strip()
                changes.append(
                    PRFileChange(path=new_path, status=status, old_path=old_path)
                )
            elif len(parts) >= 2:
                path = parts[1].strip()
                changes.append(PRFileChange(path=path, status=status))
        return changes

    def _parse_diff_stat_output(self, output: str) -> PRDiffStats:
        """Parse git diff --stat output."""
        files: list[PRFileStat] = []
        total_files = 0
        total_insertions = 0
        total_deletions = 0

        if not output:
            return PRDiffStats(
                files=[],
                total_files=0,
                total_insertions=0,
                total_deletions=0,
            )

        for line in output.splitlines():
            line = line.rstrip()
            if not line:
                continue
            if "file changed" in line:
                match = re.search(
                    r"(?P<files>\d+) file(s)? changed"
                    r"(, (?P<insertions>\d+) insertions\(\+\))?"
                    r"(, (?P<deletions>\d+) deletions\(-\))?",
                    line,
                )
                if match:
                    total_files = int(match.group("files") or 0)
                    total_insertions = int(match.group("insertions") or 0)
                    total_deletions = int(match.group("deletions") or 0)
                continue

            if "|" not in line:
                continue
            path_part, changes_part = line.split("|", 1)
            path = path_part.strip()
            change_symbols = changes_part.strip()
            insertions = change_symbols.count("+")
            deletions = change_symbols.count("-")
            files.append(
                PRFileStat(path=path, insertions=insertions, deletions=deletions)
            )

        if total_files == 0:
            total_files = len(files)
        if total_insertions == 0 and total_deletions == 0:
            total_insertions = sum(stat.insertions for stat in files)
            total_deletions = sum(stat.deletions for stat in files)

        return PRDiffStats(
            files=files,
            total_files=total_files,
            total_insertions=total_insertions,
            total_deletions=total_deletions,
        )

    def _format_pr_context_sections(
        self, pr_context: PRContext, include_patches: bool
    ) -> list[str]:
        """Format PR context sections."""
        commit_list = pr_context.commits[:20]
        commit_lines = "\n".join(f"- {commit}" for commit in commit_list)
        if len(pr_context.commits) > len(commit_list):
            commit_lines += (
                f"\n... and {len(pr_context.commits) - len(commit_list)} more"
            )

        file_sections = self._format_files_by_category(pr_context)

        stats_lines = [
            f"Total files: {pr_context.diff_stats.total_files}",
            f"Insertions: {pr_context.diff_stats.total_insertions}",
            f"Deletions: {pr_context.diff_stats.total_deletions}",
        ]
        churn_sorted = sorted(
            pr_context.diff_stats.files, key=lambda stat: stat.churn, reverse=True
        )
        top_stats = churn_sorted[:10]
        if top_stats:
            stats_lines.append("Top files by churn:")
            stats_lines.extend(
                f"- {stat.path}: +{stat.insertions} -{stat.deletions}"
                for stat in top_stats
            )

        sections = [
            "BRANCH\n"
            f"Base: {pr_context.base_branch}\n"
            f"Current: {pr_context.current_branch}",
            "COMMITS\n"
            f"Summary: {pr_context.commit_summary}\n"
            f"Count: {len(pr_context.commits)}\n"
            f"{commit_lines}",
            "FILES CHANGED\n" + "\n".join(file_sections),
            "DIFF STATS\n" + "\n".join(stats_lines),
        ]

        if include_patches:
            sections.append(self._format_patch_section(pr_context))

        truncation = self._format_truncation_section(pr_context)
        if truncation:
            sections.append(truncation)

        return sections

    def _format_files_by_category(self, pr_context: PRContext) -> list[str]:
        """Format files changed grouped by category."""
        grouped: dict[str, list[str]] = {}
        for change in pr_context.files_changed:
            category = change.category or "other"
            grouped.setdefault(category, []).append(self._format_name_status(change))

        ordered_categories = [
            "config",
            "cli",
            "infra",
            "tests",
            "docs",
            "other",
        ]
        lines: list[str] = []
        for category in ordered_categories:
            if category not in grouped:
                continue
            lines.append(f"{category.upper()}:")
            lines.extend(f"  {entry}" for entry in grouped[category])
        return lines

    def _format_name_status(self, change: PRFileChange) -> str:
        """Format name-status entry."""
        if change.old_path:
            return f"{change.status} {change.old_path} -> {change.path}"
        return f"{change.status} {change.path}"

    def _format_patch_section(self, pr_context: PRContext) -> str:
        """Format patch excerpts section."""
        if not pr_context.patch_excerpt:
            return "PATCH EXCERPTS\n(No patch excerpts included.)"
        lines = ["PATCH EXCERPTS"]
        for excerpt in pr_context.patch_excerpt:
            header = f"File: {excerpt.path}"
            if excerpt.reason:
                header = f"{header} ({excerpt.reason})"
            lines.append(header)
            lines.append(excerpt.excerpt)
        return "\n".join(lines)

    def _format_truncation_section(self, pr_context: PRContext) -> str:
        """Format truncation section."""
        if not pr_context.is_truncated:
            return ""
        return self._build_truncation_notice(
            pr_context.excluded_files, pr_context.truncation_notes
        )

    def _build_truncation_notice(
        self, excluded_files: list[str], notes: list[str]
    ) -> str:
        """Build truncation notice section."""
        lines = ["TRUNCATION NOTICE"]
        if notes:
            lines.extend(f"- {note}" for note in notes)
        if excluded_files:
            lines.append("Excluded files:")
            lines.extend(f"- {path}" for path in excluded_files)
        return "\n".join(lines)

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
                    ["git", "log", "--oneline", f"{base_branch}..HEAD"]
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
