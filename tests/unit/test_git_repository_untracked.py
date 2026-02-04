import subprocess
from pathlib import Path

from ai_cli.config.settings import GitConfig
from ai_cli.infrastructure.git_repository import GitRepository


def _run_git(repo_dir: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )


def _setup_repo(tmp_path: Path) -> Path:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _run_git(repo_dir, "init")
    _run_git(repo_dir, "config", "user.email", "tests@example.com")
    _run_git(repo_dir, "config", "user.name", "Test User")
    return repo_dir


def test_get_all_changes_lists_untracked_files_individually(monkeypatch, tmp_path):
    repo_dir = _setup_repo(tmp_path)
    module_dir = repo_dir / "new_module"
    module_dir.mkdir()
    (module_dir / "__init__.py").write_text("", encoding="utf-8")
    (module_dir / "a.py").write_text("VALUE = 1\n", encoding="utf-8")

    monkeypatch.setenv("AI_CLI_WORK_DIR", str(repo_dir))
    repo = GitRepository(GitConfig(max_diff_size=100000, default_branch="main"))

    changes = repo.get_all_changes()
    paths = {change.path for change in changes}

    assert "new_module/__init__.py" in paths
    assert "new_module/a.py" in paths
    assert "new_module" not in paths


def test_get_diff_for_files_includes_untracked_new_file_patches(monkeypatch, tmp_path):
    repo_dir = _setup_repo(tmp_path)
    module_dir = repo_dir / "new_module"
    module_dir.mkdir()
    (module_dir / "__init__.py").write_text("", encoding="utf-8")
    (module_dir / "a.py").write_text("VALUE = 1\n", encoding="utf-8")

    monkeypatch.setenv("AI_CLI_WORK_DIR", str(repo_dir))
    repo = GitRepository(GitConfig(max_diff_size=100000, default_branch="main"))

    # Simulate a caller passing a directory path; repository should expand it.
    diff = repo.get_diff_for_files(["new_module"])

    assert (
        "diff --git a/new_module/__init__.py b/new_module/__init__.py" in diff.content
    )
    assert "diff --git a/new_module/a.py b/new_module/a.py" in diff.content
    assert "new file mode" in diff.content
