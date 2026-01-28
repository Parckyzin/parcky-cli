from typer.testing import CliRunner

from ai_cli.cli import main as cli_main
from ai_cli.cli.handlers import config_cmd
from ai_cli.config import paths
from ai_cli.config.writer import read_env_value, set_env_value


def _patch_paths(monkeypatch, global_path) -> None:
    monkeypatch.setattr(config_cmd, "get_global_env_path", lambda: global_path)
    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_path)


def _patch_needs_init(monkeypatch, value: bool) -> None:
    monkeypatch.setattr(config_cmd, "needs_init", lambda *_args, **_kwargs: value)


def test_config_list_shows_values_and_sources(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    set_env_value(global_path, "AI_MAX_CONTEXT_CHARS", "12345")
    set_env_value(global_path, "GIT_MAX_DIFF_SIZE", "200")

    _patch_paths(monkeypatch, global_path)
    _patch_needs_init(monkeypatch, False)
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
    _patch_needs_init(monkeypatch, False)
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
    _patch_needs_init(monkeypatch, False)
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: "Exit")

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-e"])

    assert result.exit_code == 0


def test_config_edit_ai_max_context_chars_persists(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_needs_init(monkeypatch, False)

    entry = next(
        e for e in config_cmd.list_config_entries(global_path)
        if e.key == "ai_max_context_chars"
    )
    categories = iter(["AI limits", "Exit"])
    selections = iter([entry, None])
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: next(categories))
    monkeypatch.setattr(config_cmd, "_select_edit_entry", lambda _entries, title: next(selections))
    monkeypatch.setattr(config_cmd, "prompt", lambda *_args, **_kwargs: "12000")
    monkeypatch.setattr(config_cmd, "modal_confirm", lambda **_kwargs: True)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-e"])

    assert result.exit_code == 0
    assert read_env_value(global_path, "AI_MAX_CONTEXT_CHARS") == "12000"


def test_config_edit_cancel_does_not_persist(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_needs_init(monkeypatch, False)

    entry = next(
        e for e in config_cmd.list_config_entries(global_path)
        if e.key == "git_max_diff_size"
    )
    categories = iter(["Git limits", "Exit"])
    selections = iter([entry, None])
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: next(categories))
    monkeypatch.setattr(config_cmd, "_select_edit_entry", lambda _entries, title: next(selections))
    monkeypatch.setattr(config_cmd, "prompt", lambda *_args, **_kwargs: "120")
    monkeypatch.setattr(config_cmd, "modal_confirm", lambda **_kwargs: False)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-e"])

    assert result.exit_code == 0
    assert read_env_value(global_path, "GIT_MAX_DIFF_SIZE") == ""


def test_config_edit_rejects_invalid_value(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_needs_init(monkeypatch, False)

    entry = next(
        e for e in config_cmd.list_config_entries(global_path)
        if e.key == "git_max_diff_size"
    )
    categories = iter(["Git limits", "Exit"])
    selections = iter([entry, None])
    inputs = iter(["0", ""])
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: next(categories))
    monkeypatch.setattr(config_cmd, "_select_edit_entry", lambda _entries, title: next(selections))
    monkeypatch.setattr(config_cmd, "prompt", lambda *_args, **_kwargs: next(inputs))
    monkeypatch.setattr(config_cmd, "modal_confirm", lambda **_kwargs: True)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-e"])

    assert result.exit_code == 0
    assert "must be at least" in result.output
    assert read_env_value(global_path, "GIT_MAX_DIFF_SIZE") == ""


def test_config_triggers_init_when_needed(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_needs_init(monkeypatch, True)

    called = {"init": False}

    monkeypatch.setattr(config_cmd, "needs_init", lambda *_args, **_kwargs: True)

    def _fake_init(_path):
        called["init"] = True

    monkeypatch.setattr(config_cmd, "_run_init_flow", _fake_init)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config"])

    assert result.exit_code == 0
    assert called["init"] is True


def test_config_init_persists_values(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_needs_init(monkeypatch, False)

    def _set_keys(path):
        config_cmd.set_provider_api_key(path, config_cmd.AvailableProviders.OPENAI, "key")

    def _configure(path):
        _set_keys(path)
        return True

    monkeypatch.setattr(config_cmd, "_configure_provider_keys", _configure)
    monkeypatch.setattr(
        config_cmd, "_select_active_provider", lambda _path: "openai"
    )
    monkeypatch.setattr(
        config_cmd, "_select_model_name", lambda _provider: "gpt-4o"
    )
    monkeypatch.setattr(
        config_cmd,
        "_prompt_int_value",
        lambda **_kwargs: 12000,
    )
    monkeypatch.setattr(config_cmd, "modal_confirm", lambda **_kwargs: True)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "init"])

    assert result.exit_code == 0
    assert read_env_value(global_path, "AI_PROVIDER") == "openai"
    assert read_env_value(global_path, "AI_MODEL") == "gpt-4o"
    assert read_env_value(global_path, "AI_MAX_CONTEXT_CHARS") == "12000"
    assert read_env_value(global_path, "GIT_MAX_DIFF_SIZE") == "12000"


def test_init_filters_ready_providers(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")
    set_env_value(global_path, "GOOGLE_API_KEY", "key")

    _patch_paths(monkeypatch, global_path)
    _patch_needs_init(monkeypatch, True)

    captured: dict[str, list[str]] = {}

    def _capture_provider_select(*, current=None, providers=None, **_kwargs):
        captured["providers"] = [p.value for p in (providers or [])]
        return None

    monkeypatch.setattr(config_cmd, "prompt_provider_select", _capture_provider_select)
    monkeypatch.setattr(config_cmd, "_configure_provider_keys", lambda _p: True)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "init"])

    assert result.exit_code == 0
    assert "google" in captured["providers"]
    assert "openai" not in captured["providers"]
    assert "anthropic" not in captured["providers"]


def test_init_cancel_stops_flow(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)
    _patch_needs_init(monkeypatch, True)

    called = {"provider": False}

    monkeypatch.setattr(config_cmd, "_configure_provider_keys", lambda _p: False)

    def _select_provider(_path):
        called["provider"] = True
        return "openai"

    monkeypatch.setattr(config_cmd, "_select_active_provider", _select_provider)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "init"])

    assert result.exit_code == 0
    assert called["provider"] is False


def test_model_catalog_used_for_init(monkeypatch) -> None:
    captured: list[str] = []

    def _fake_list_models(_self, _provider, _api_key):
        return ["m1", "m2"]

    def _fake_select(models, _current, on_select, **_kwargs):
        captured.extend(models)
        on_select("m2")

    monkeypatch.setattr(config_cmd.ModelCatalog, "list_models", _fake_list_models)
    monkeypatch.setattr(config_cmd, "interactive_model_select", _fake_select)
    monkeypatch.setattr(config_cmd, "_resolve_provider_api_key", lambda _p: "key")

    result = config_cmd._select_model_name("google")
    assert result == "m2"
    assert captured == ["m1", "m2"]


def test_model_catalog_not_called_without_key(monkeypatch) -> None:
    called = {"list": False}

    def _fake_list_models(_self, _provider, _api_key):
        called["list"] = True
        return []

    monkeypatch.setattr(config_cmd.ModelCatalog, "list_models", _fake_list_models)
    monkeypatch.setattr(config_cmd, "_resolve_provider_api_key", lambda _p: None)

    result = config_cmd._select_model_name("openai")
    assert result is None
    assert called["list"] is False
