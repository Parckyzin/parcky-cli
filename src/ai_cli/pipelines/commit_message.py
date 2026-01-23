from collections.abc import Sequence

from ai_cli.core.models import GitDiff

from .common import dedupe_preserve, format_section, stable_sorted, truncate_lines


def extract_files_from_diff(diff_content: str) -> list[str]:
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
    return stable_sorted(dedupe_preserve(files))


def build_commit_context(
    diff: GitDiff,
    file_paths: Sequence[str] | None = None,
    *,
    max_files: int = 20,
    max_example_lines: int = 120,
) -> str:
    """Build a structured, size-limited commit context for AI."""
    files = (
        stable_sorted(dedupe_preserve(file_paths))
        if file_paths
        else extract_files_from_diff(diff.content)
    )
    summary_body_lines = [
        f"Files changed: {len(files)}",
    ]
    for file_path in files[:max_files]:
        summary_body_lines.append(f"- {file_path}")
    if len(files) > max_files:
        summary_body_lines.append(f"... and {len(files) - max_files} more")

    example_lines = diff.content.splitlines()
    truncated_lines, examples_truncated = truncate_lines(
        example_lines, max_example_lines
    )
    examples = "\n".join(truncated_lines).strip()
    if not examples:
        examples = "No diff available."

    summary_section = format_section("SUMMARY", "\n".join(summary_body_lines))
    examples_section = format_section("EXAMPLES", examples)

    context_parts = [summary_section, examples_section]

    notes: list[str] = []
    if diff.is_truncated:
        notes.append("Original diff was truncated.")
    if examples_truncated:
        notes.append(f"Diff examples truncated to {max_example_lines} lines.")
    if notes:
        context_parts.append("NOTE: " + " ".join(notes))

    return "\n\n".join(context_parts)
