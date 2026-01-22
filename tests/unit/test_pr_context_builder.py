"""
Unit tests for PR context parsing and truncation.
"""

from ai_cli.config.settings import GitConfig
from ai_cli.core.models import PRDiffStats, PRFileChange, PRFileStat
from ai_cli.infrastructure.git_repository import GitRepository
from ai_cli.services.pr_context_builder import build_pr_context


def test_parse_name_status_with_rename():
    repo = GitRepository(GitConfig(max_diff_size=1000, default_branch="main"))
    output = "M\tREADME.md\nR100\tsrc/old.py\tsrc/new.py\nA\tsrc/added.py"

    parsed = repo._parse_name_status(output)

    assert parsed[0].status == "M"
    assert parsed[1].status.startswith("R")
    assert parsed[1].old_path == "src/old.py"
    assert parsed[1].path == "src/new.py"
    assert parsed[2].status == "A"


def test_parse_diff_stat_output():
    repo = GitRepository(GitConfig(max_diff_size=1000, default_branch="main"))
    output = "\n".join(
        [
            "src/app.py | 4 ++--",
            "docs/README.md | 2 ++",
            "2 files changed, 6 insertions(+), 2 deletions(-)",
        ]
    )

    stats = repo._parse_diff_stat_output(output)

    assert stats.total_files == 2
    assert stats.total_insertions == 4
    assert stats.total_deletions == 2
    assert stats.files[0].path == "src/app.py"


def test_pr_context_truncation_prioritizes_important_files(monkeypatch):
    repo = GitRepository(GitConfig(max_diff_size=1000, default_branch="main"))

    def fake_patch(_base_branch: str, file_path: str) -> str:
        return "\n".join(
            [
                f"diff --git a/{file_path} b/{file_path}",
                f"--- a/{file_path}",
                f"+++ b/{file_path}",
                "@@",
                "+change",
            ]
        )

    monkeypatch.setattr(repo, "get_branch_patch", fake_patch)

    files = [
        PRFileChange(path="src/ai_cli/cli/main.py", status="M"),
        PRFileChange(path="AGENTS.MD", status="A"),
        PRFileChange(path="src/ai_cli/config/settings.py", status="M"),
        PRFileChange(path="src/ai_cli/services/foo.py", status="M"),
        PRFileChange(path="tests/test_sample.py", status="M"),
    ]
    stats = PRDiffStats(
        files=[
            PRFileStat(path=change.path, insertions=10, deletions=2) for change in files
        ],
        total_files=len(files),
        total_insertions=50,
        total_deletions=10,
    )

    pr_context = build_pr_context(
        git_repo=repo,
        base_branch="main",
        current_branch="feature/test",
        commits=["feat: change things", "chore: update configs"],
        files_changed=files,
        diff_stats=stats,
        max_context_chars=1200,
    )

    assert pr_context.is_truncated is True
    assert pr_context.excluded_files
    assert any(
        excerpt.path == "src/ai_cli/cli/main.py" for excerpt in pr_context.patch_excerpt
    )
    assert any(excerpt.path == "AGENTS.MD" for excerpt in pr_context.patch_excerpt)

    context_text = repo.build_ai_context(pr_context, max_context_chars=600)
    for change in files:
        assert change.path in context_text
    assert "Total files: 5" in context_text
    assert "Insertions: 50" in context_text
    assert "Deletions: 10" in context_text
    assert "feat: change things" in context_text
    assert "TRUNCATION NOTICE" in context_text
