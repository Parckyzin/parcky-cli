from __future__ import annotations

from ai_cli.core.models import (
    PRContext,
    PRDiffStats,
    PRFileChange,
    PRPatchExcerpt,
)
from ai_cli.infrastructure.git_repository import GitRepository


def build_pr_context(
    git_repo: GitRepository,
    base_branch: str,
    current_branch: str,
    commits: list[str],
    files_changed: list[PRFileChange],
    diff_stats: PRDiffStats,
    max_context_chars: int,
) -> PRContext:
    """Build a PRContext with curated patch excerpts."""
    commit_summary = "; ".join(commits[:5])
    if len(commits) > 5:
        commit_summary += f" (+{len(commits) - 5} more)"

    categorized_files = [_apply_category(change) for change in files_changed]

    patch_candidates = _prioritize_files(categorized_files, diff_stats)
    patch_excerpts: list[PRPatchExcerpt] = []
    excluded_files: list[str] = []

    base_text = _render_base_sections(
        base_branch,
        current_branch,
        commits,
        commit_summary,
        categorized_files,
        diff_stats,
    )
    base_text = f"{base_text}\n\nPATCH EXCERPTS\n"
    base_length = len(base_text)
    budget = max_context_chars - base_length

    if budget <= 0:
        return PRContext(
            base_branch=base_branch,
            current_branch=current_branch,
            commits=commits,
            commit_summary=commit_summary,
            files_changed=categorized_files,
            diff_stats=diff_stats,
            patch_excerpt=[],
            is_truncated=True,
            excluded_files=[change.path for change in categorized_files],
            truncation_notes=[
                "Base context exceeded the maximum size; no patches included."
            ],
        )

    for candidate in patch_candidates:
        patch = git_repo.get_branch_patch(base_branch, candidate.path)
        excerpt = _excerpt_patch(patch, max_lines=140)
        excerpt_text = f"File: {candidate.path}\n{excerpt}"
        if len(excerpt_text) > budget:
            excluded_files.append(candidate.path)
            continue
        patch_excerpts.append(
            PRPatchExcerpt(
                path=candidate.path,
                excerpt=excerpt,
                reason=_patch_reason(candidate),
            )
        )
        budget -= len(excerpt_text)

    is_truncated = len(excluded_files) > 0
    truncation_notes = []
    if is_truncated:
        truncation_notes.append(
            "Some patches were excluded to respect the context size budget."
        )

    return PRContext(
        base_branch=base_branch,
        current_branch=current_branch,
        commits=commits,
        commit_summary=commit_summary,
        files_changed=categorized_files,
        diff_stats=diff_stats,
        patch_excerpt=patch_excerpts,
        is_truncated=is_truncated,
        excluded_files=excluded_files,
        truncation_notes=truncation_notes,
    )


def _apply_category(change: PRFileChange) -> PRFileChange:
    """Apply category classification to a file change."""
    return PRFileChange(
        path=change.path,
        status=change.status,
        old_path=change.old_path,
        category=_categorize_path(change.path),
    )


def _categorize_path(path: str) -> str:
    """Categorize file paths for PR context grouping."""
    normalized = path.lower()
    if normalized.startswith("docs/") or normalized.endswith(".md"):
        return "docs"
    if normalized.startswith("tests/") or "test_" in normalized:
        return "tests"
    if normalized.startswith("src/ai_cli/cli/"):
        return "cli"
    if normalized.startswith("src/ai_cli/infrastructure/"):
        return "infra"
    if normalized.startswith("src/ai_cli/config/") or normalized.endswith(".env"):
        return "config"
    if normalized.startswith(".github/") or normalized.startswith("scripts/"):
        return "config"
    if normalized in {"makefile", "pyproject.toml", "uv.lock"}:
        return "config"
    return "other"


def _prioritize_files(
    files: list[PRFileChange], diff_stats: PRDiffStats
) -> list[PRFileChange]:
    """Prioritize files for patch excerpts."""
    churn_map = {stat.path: stat.churn for stat in diff_stats.files}

    def churn_value(change: PRFileChange) -> int:
        return churn_map.get(change.path, 0)

    priority = [change for change in files if _is_priority_file(change.path)]
    remaining = [change for change in files if change not in priority]
    remaining_sorted = sorted(remaining, key=churn_value, reverse=True)
    return priority + remaining_sorted


def _is_priority_file(path: str) -> bool:
    """Check whether a file should always be included in patch excerpts."""
    normalized = path.lower()
    return (
        normalized.startswith("src/ai_cli/cli/")
        or normalized.startswith("src/ai_cli/config/")
        or normalized.startswith("src/ai_cli/core/interfaces/")
        or normalized.endswith("agents.md")
        or normalized.endswith("readme.md")
        or normalized.startswith(".github/")
        or normalized.startswith("scripts/")
        or normalized in {"pyproject.toml", "uv.lock", "makefile"}
    )


def _patch_reason(change: PRFileChange) -> str:
    """Explain why a patch was included."""
    if change.category in {"config", "cli", "docs"}:
        return f"priority {change.category}"
    return "high churn"


def _excerpt_patch(patch: str, max_lines: int = 140) -> str:
    """Curate patch excerpts to focus on high-signal hunks."""
    if not patch:
        return "(empty patch)"
    lines = patch.splitlines()
    excerpt_lines: list[str] = []
    for line in lines:
        if (
            line.startswith("diff --git")
            or line.startswith("index ")
            or line.startswith("---")
            or line.startswith("+++")
            or line.startswith("@@")
            or line.startswith(("+", "-", " "))
        ):
            excerpt_lines.append(line)
        if len(excerpt_lines) >= max_lines:
            break
    if len(excerpt_lines) < len(lines):
        excerpt_lines.append("...[PATCH EXCERPT TRUNCATED]...")
    return "\n".join(excerpt_lines)


def _render_base_sections(
    base_branch: str,
    current_branch: str,
    commits: list[str],
    commit_summary: str,
    files_changed: list[PRFileChange],
    diff_stats: PRDiffStats,
) -> str:
    """Render base context sections to estimate size."""
    commit_list = commits[:20]
    commit_lines = "\n".join(f"- {commit}" for commit in commit_list)
    if len(commits) > len(commit_list):
        commit_lines += f"\n... and {len(commits) - len(commit_list)} more"

    files_lines = "\n".join(
        f"- {change.status} {change.path}" for change in files_changed
    )
    stats_lines = [
        f"Total files: {diff_stats.total_files}",
        f"Insertions: {diff_stats.total_insertions}",
        f"Deletions: {diff_stats.total_deletions}",
    ]
    top_files = sorted(diff_stats.files, key=lambda stat: stat.churn, reverse=True)[:10]
    stats_lines.extend(
        f"- {stat.path}: +{stat.insertions} -{stat.deletions}" for stat in top_files
    )

    sections = [
        f"BRANCH\nBase: {base_branch}\nCurrent: {current_branch}",
        f"COMMITS\nSummary: {commit_summary}\n{commit_lines}",
        f"FILES CHANGED\n{files_lines}",
        "DIFF STATS\n" + "\n".join(stats_lines),
    ]
    return "\n\n".join(sections)
