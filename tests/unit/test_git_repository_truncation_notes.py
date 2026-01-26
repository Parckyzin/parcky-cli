from ai_cli.config.settings import GitConfig
from ai_cli.infrastructure.git_repository import GitRepository


def test_get_staged_diff_includes_truncation_notes(monkeypatch):
    config = GitConfig(max_diff_size=10, default_branch="main")
    repo = GitRepository(config)
    long_diff = "x" * 50

    monkeypatch.setattr(repo, "_run_command", lambda _cmd: long_diff)

    diff = repo.get_staged_diff()

    assert diff.is_truncated is True
    assert diff.truncation_notes == [
        "Diff truncated by GitRepository (max_diff_size=10)."
    ]
