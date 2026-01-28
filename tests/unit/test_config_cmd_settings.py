from types import SimpleNamespace

from typer.testing import CliRunner

from ai_cli.cli import main as cli_main
from ai_cli.cli.handlers import config_cmd
from ai_cli.config import paths
from ai_cli.config.writer import read_env_value, set_env_value


def _patch_paths(monkeypatch, global_path) -> None:
    monkeypatch.setattr(config_cmd, "get_global_env_path", lambda: global_path)
    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_path)


def _patch_context(monkeypatch) -> None:
    monkeypatch.setattr(
        config_cmd,
        "get_context",
        lambda: SimpleNamespace(config=SimpleNamespace(debug=False)),
    )


def test_config_list_shows_values_and_sources(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    set_env_value(global_path, "AI_MAX_CONTEXT_CHARS", "12345")
    set_env_value(global_path, "GIT_MAX_DIFF_SIZE", "200")

    _patch_paths(monkeypatch, global_path)
    _patch_context(monkeypatch)
    monkeypatch.setattr(
        config_cmd, "prompt", lambda _msg: (_ for _ in ()).throw(AssertionError)
    )

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config"])

    assert result.exit_code == 0
    assert "ai_max_context_chars" in result.output
    assert "12345" in result.output
    assert "git_max_diff_size" in result.output
    assert "200" in result.output
    assert "global" in result.output
    assert "Tip: To edit editable values, run: parcky-cli config -e" in result.output


def test_config_read_only_does_not_touch_prompt(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_context(monkeypatch)
    monkeypatch.setattr(
        config_cmd, "prompt", lambda _msg: (_ for _ in ()).throw(AssertionError)
    )

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config"])

    assert result.exit_code == 0
    assert "Tip: To edit editable values, run: parcky-cli config -e" in result.output


def test_config_edit_flow_basic_exit(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_context(monkeypatch)
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: "Exit")

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-e"])

    assert result.exit_code == 0


def test_config_edit_ai_max_context_chars_persists(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_context(monkeypatch)

    entry = next(
        e for e in config_cmd.list_config_entries(global_path)
        if e.key == "ai_max_context_chars"
    )
    categories = iter(["AI limits", "Exit"])
    selections = iter([entry, None])
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: next(categories))
    monkeypatch.setattr(config_cmd, "_select_edit_entry", lambda _entries, title: next(selections))
    monkeypatch.setattr(config_cmd, "prompt", lambda _msg: "12000")
    monkeypatch.setattr(config_cmd, "modal_confirm", lambda **_kwargs: True)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-e"])

    assert result.exit_code == 0
    assert read_env_value(global_path, "AI_MAX_CONTEXT_CHARS") == "12000"


def test_config_edit_cancel_does_not_persist(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_context(monkeypatch)

    entry = next(
        e for e in config_cmd.list_config_entries(global_path)
        if e.key == "git_max_diff_size"
    )
    categories = iter(["Git limits", "Exit"])
    selections = iter([entry, None])
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: next(categories))
    monkeypatch.setattr(config_cmd, "_select_edit_entry", lambda _entries, title: next(selections))
    monkeypatch.setattr(config_cmd, "prompt", lambda _msg: "120")
    monkeypatch.setattr(config_cmd, "modal_confirm", lambda **_kwargs: False)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-e"])

    assert result.exit_code == 0
    assert read_env_value(global_path, "GIT_MAX_DIFF_SIZE") == ""


def test_config_edit_rejects_invalid_value(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_context(monkeypatch)

    entry = next(
        e for e in config_cmd.list_config_entries(global_path)
        if e.key == "git_max_diff_size"
    )
    categories = iter(["Git limits", "Exit"])
    selections = iter([entry, None])
    inputs = iter(["0", ""])
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: next(categories))
    monkeypatch.setattr(config_cmd, "_select_edit_entry", lambda _entries, title: next(selections))
    monkeypatch.setattr(config_cmd, "prompt", lambda _msg: next(inputs))
    monkeypatch.setattr(config_cmd, "modal_confirm", lambda **_kwargs: True)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-e"])

    assert result.exit_code == 0
    assert "must be at least" in result.output
    assert read_env_value(global_path, "GIT_MAX_DIFF_SIZE") == ""
