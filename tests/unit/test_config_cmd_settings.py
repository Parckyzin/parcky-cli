from types import SimpleNamespace

from typer.testing import CliRunner

from ai_cli.cli import main as cli_main
from ai_cli.cli.handlers import config_cmd
from ai_cli.config import paths
from ai_cli.config import loader
from ai_cli.config.writer import read_env_value, set_env_value


def _patch_paths(monkeypatch, local_path, global_path) -> None:
    monkeypatch.setattr(config_cmd, "get_local_env_path", lambda: local_path)
    monkeypatch.setattr(config_cmd, "get_global_env_path", lambda: global_path)
    monkeypatch.setattr(paths, "get_local_env_path", lambda: local_path)
    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_path)


def _patch_context(monkeypatch) -> None:
    monkeypatch.setattr(
        config_cmd,
        "get_context",
        lambda: SimpleNamespace(config=SimpleNamespace(debug=False)),
    )


def test_config_list_shows_values_and_sources(tmp_path, monkeypatch) -> None:
    local_path = tmp_path / ".env"
    global_path = tmp_path / "global.env"
    set_env_value(local_path, "AI_MAX_CONTEXT_CHARS", "12345")
    set_env_value(global_path, "GIT_MAX_DIFF_SIZE", "200")

    _patch_paths(monkeypatch, local_path, global_path)
    _patch_context(monkeypatch)
    monkeypatch.setattr(config_cmd, "prompt", lambda _msg: "")

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config"])

    assert result.exit_code == 0
    assert "ai_max_context_chars" in result.output
    assert "12345" in result.output
    assert "local" in result.output
    assert "git_max_diff_size" in result.output
    assert "200" in result.output
    assert "global" in result.output


def test_config_update_ai_max_context_chars_persists(tmp_path, monkeypatch) -> None:
    local_path = tmp_path / ".env"
    global_path = tmp_path / "global.env"
    local_path.write_text("")

    _patch_paths(monkeypatch, local_path, global_path)
    _patch_context(monkeypatch)

    inputs = iter(["1", "12000"])
    monkeypatch.setattr(config_cmd, "prompt", lambda _msg: next(inputs))

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config"])

    assert result.exit_code == 0
    assert read_env_value(local_path, "AI_MAX_CONTEXT_CHARS") == "12000"

    settings_dict = loader.build_settings_dict()
    assert settings_dict["ai"]["max_context_chars"] == 12000


def test_config_invalid_git_max_diff_size_not_persisted(
    tmp_path, monkeypatch
) -> None:
    local_path = tmp_path / ".env"
    global_path = tmp_path / "global.env"
    local_path.write_text("")

    _patch_paths(monkeypatch, local_path, global_path)
    _patch_context(monkeypatch)

    inputs = iter(["2", "abc", ""])
    monkeypatch.setattr(config_cmd, "prompt", lambda _msg: next(inputs))

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config"])

    assert result.exit_code == 0
    assert "Please enter a valid integer" in result.output
    assert read_env_value(local_path, "GIT_MAX_DIFF_SIZE") == ""
