from collections.abc import Sequence

from ai_cli.core.models import FileChange, FileGroup

from .common import safe_truncate, stable_sorted


def _sort_changes(changes: Sequence[FileChange]) -> list[FileChange]:
    return stable_sorted(changes, key=lambda change: (change.folder, change.path))


def _sort_groups(groups: Sequence[FileGroup]) -> list[FileGroup]:
    return stable_sorted(groups, key=lambda group: group.group_key)


def build_file_correlation_prompt(
    prompt_template: str,
    *,
    folder: str,
    files: Sequence[FileChange],
    diff_content: str,
    max_diff_chars: int = 3000,
) -> str:
    """Build the prompt for file correlation analysis."""
    ordered_files = _sort_changes(files)
    files_list = "\n".join(f"- {f.path} ({f.status})" for f in ordered_files)
    if not diff_content:
        diff_excerpt = "No diff available"
    else:
        diff_excerpt, _ = safe_truncate(diff_content, max_diff_chars)

    return prompt_template.format(
        folder=folder,
        files_list=files_list,
        diff_content=diff_excerpt,
    )


def parse_group_response(
    response: str, files: Sequence[FileChange], folder: str
) -> list[FileGroup]:
    """Parse AI response to extract file groups."""
    ordered_files = _sort_changes(files)
    groups: list[FileGroup] = []
    file_map = {f.path: f for f in ordered_files}
    file_basenames = {f.filename: f for f in ordered_files}
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
            if name in file_map and name not in assigned_files:
                group_files.append(file_map[name])
                assigned_files.add(name)
            elif name in file_basenames:
                full_path = file_basenames[name].path
                if full_path not in assigned_files:
                    group_files.append(file_basenames[name])
                    assigned_files.add(full_path)

        if group_files:
            groups.append(
                FileGroup(
                    files=_sort_changes(group_files),
                    folder=folder,
                    explanation="Grouped by AI correlation within the folder.",
                )
            )

    for file in ordered_files:
        if file.path not in assigned_files:
            groups.append(
                FileGroup(
                    files=[file],
                    folder=folder,
                    explanation="No correlation found; kept separate.",
                )
            )

    if not groups:
        return [
            FileGroup(
                files=ordered_files,
                folder=folder,
                explanation="Grouped by folder (no correlation output).",
            )
        ]

    return _sort_groups(groups)
