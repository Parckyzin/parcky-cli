from collections.abc import Sequence

from ai_cli.core.models import GitDiff

from .common import (
    dedupe_preserve,
    format_notes,
    format_section,
    safe_truncate,
    stable_sorted,
    truncate_lines,
)


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
    max_context_chars: int | None = None,
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
    notes: list[str] = []
    if diff.is_truncated:
        notes.append("Diff was truncated.")
    if diff.truncation_notes:
        notes.extend(diff.truncation_notes)
    if examples_truncated:
        notes.append(f"Diff examples truncated to {max_example_lines} lines.")

    max_notes = 8
    if len(notes) > max_notes:
        notes = list(notes[:max_notes]) + [
            f"... and {len(notes) - max_notes} more notes"
        ]

    notes_section = format_notes(notes)
    context_parts = [summary_section, examples_section, notes_section]

    def _join(parts: list[str]) -> str:
        return "\n\n".join(part for part in parts if part)

    full_context = _join(context_parts)
    if max_context_chars is None or len(full_context) <= max_context_chars:
        return full_context

    notes.append(f"Context truncated to {max_context_chars} chars.")
    notes_section = format_notes(notes)

    base_context = _join([summary_section, examples_section])
    reserved = len(notes_section) + (2 if base_context else 0)
    available = max_context_chars - reserved
    if available <= 0:
        truncated_notes, _ = safe_truncate(notes_section, max_context_chars)
        return truncated_notes

    truncated_base, _ = safe_truncate(base_context, available)
    if notes_section:
        return (
            f"{truncated_base}\n\n{notes_section}" if truncated_base else notes_section
        )
    return truncated_base
