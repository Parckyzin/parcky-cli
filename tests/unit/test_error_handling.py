"""
Unit tests for error handling behavior.
"""

from subprocess import CalledProcessError

import pytest
from typer.testing import CliRunner

from ai_cli.cli import main as cli_main
from ai_cli.cli.handlers import create_repo as create_repo_handler
from ai_cli.core.exceptions import (
    ExitCode,
    GitError,
    NoStagedChangesError,
    RepositoryError,
)
from ai_cli.infrastructure import git_repository
from ai_cli.infrastructure.git_repository import GitRepository


def test_get_staged_diff_no_changes_raises_usage_error(mock_git_config, monkeypatch):
    """Return a usage error when no staged changes exist."""
    repo = GitRepository(mock_git_config)
    monkeypatch.setattr(repo, "_run_command", lambda _: "")

    with pytest.raises(NoStagedChangesError) as exc:
        repo.get_staged_diff()

    assert exc.value.exit_code == ExitCode.USAGE_ERROR
    assert "No staged changes" in exc.value.user_message


def test_git_command_failure_maps_to_git_error(mock_git_config, monkeypatch):
    """Map subprocess errors to GitError with a friendly message."""
    repo = GitRepository(mock_git_config)

    def fake_run(*_args, **_kwargs):
        raise CalledProcessError(1, ["git", "status"], stderr="boom")

    monkeypatch.setattr(git_repository.subprocess, "run", fake_run)

    with pytest.raises(GitError) as exc:
        repo._run_command(["git", "status"])

    assert exc.value.exit_code == ExitCode.EXTERNAL_ERROR
    assert "Git command failed" in str(exc.value)
    assert "Git command failed" in exc.value.user_message


def test_cli_create_repo_invalid_visibility_exits_with_usage_error():
    """CLI should return usage exit code for invalid visibility."""
    runner = CliRunner()
    result = runner.invoke(
        cli_main.app,
        ["create-repo", "my-repo", "--visibility", "invalid"],
    )

    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Invalid visibility" in result.output
    assert "Traceback" not in result.output


def test_cli_create_repo_external_error_exits_with_external_code(monkeypatch):
    """CLI should use external exit code when repo creation fails."""
    runner = CliRunner()

    def fake_check(_self):
        return None

    def fake_create(_self, _repo):
        raise RepositoryError(
            "GitHub CLI command failed: boom",
            user_message="GitHub CLI failed. Check auth.",
        )

    monkeypatch.setattr(
        create_repo_handler.GitHubRepoService, "_check_gh_cli", fake_check
    )
    monkeypatch.setattr(
        create_repo_handler.GitHubRepoService, "create_repository", fake_create
    )

    result = runner.invoke(
        cli_main.app,
        ["create-repo", "my-repo", "--visibility", "private"],
    )

    assert result.exit_code == ExitCode.EXTERNAL_ERROR
    assert "GitHub CLI failed" in result.output
    assert "Traceback" not in result.output
