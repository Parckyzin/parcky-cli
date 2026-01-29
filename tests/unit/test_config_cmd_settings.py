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
    monkeypatch.setattr(config_cmd, "_run_init_flow", lambda _path: None)
    monkeypatch.setattr(config_cmd, "needs_init", lambda *_a, **_k: False)
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
    monkeypatch.setattr(config_cmd, "_run_init_flow", lambda _path: None)
    monkeypatch.setattr(config_cmd, "needs_init", lambda *_a, **_k: False)
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
    monkeypatch.setattr(config_cmd, "_run_init_flow", lambda _path: None)
    monkeypatch.setattr(config_cmd, "needs_init", lambda *_a, **_k: False)
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
        e
        for e in config_cmd.list_config_entries(global_path)
        if e.key == "ai_max_context_chars"
    )
    categories = iter(["AI limits", "Exit"])
    selections = iter([entry, None])
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: next(categories))
    monkeypatch.setattr(
        config_cmd,
        "_select_edit_entry",
        lambda _entries, **_kwargs: next(selections),
    )
    monkeypatch.setattr(config_cmd, "numeric_input", lambda **_kwargs: 12000)
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
        e
        for e in config_cmd.list_config_entries(global_path)
        if e.key == "git_max_diff_size"
    )
    categories = iter(["Git limits", "Exit"])
    selections = iter([entry, None])
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: next(categories))
    monkeypatch.setattr(
        config_cmd,
        "_select_edit_entry",
        lambda _entries, **_kwargs: next(selections),
    )
    monkeypatch.setattr(config_cmd, "numeric_input", lambda **_kwargs: 120)
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
        e
        for e in config_cmd.list_config_entries(global_path)
        if e.key == "git_max_diff_size"
    )
    categories = iter(["Git limits", "Exit"])
    selections = iter([entry, None])
    monkeypatch.setattr(config_cmd, "_select_edit_category", lambda: next(categories))
    monkeypatch.setattr(
        config_cmd,
        "_select_edit_entry",
        lambda _entries, **_kwargs: next(selections),
    )
    monkeypatch.setattr(config_cmd, "numeric_input", lambda **_kwargs: None)
    monkeypatch.setattr(config_cmd, "modal_confirm", lambda **_kwargs: True)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-e"])

    assert result.exit_code == 0
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
        config_cmd.set_provider_api_key(
            path, config_cmd.AvailableProviders.OPENAI, "key"
        )

    def _configure(path):
        _set_keys(path)
        return True

    monkeypatch.setattr(config_cmd, "_configure_provider_keys", _configure)
    monkeypatch.setattr(config_cmd, "_select_active_provider", lambda _path: "openai")
    monkeypatch.setattr(config_cmd, "_select_model_name", lambda _provider: "gpt-4o")
    values = iter([12000, 12000])
    monkeypatch.setattr(
        config_cmd,
        "_prompt_numeric_overlay",
        lambda **_kwargs: next(values),
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

    def _capture_select(options, title=None, **_kwargs):
        captured["providers"] = [opt.value for opt in options]
        return None

    monkeypatch.setattr(config_cmd, "select", _capture_select)
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


def test_manage_keys_updates_status(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    _patch_paths(monkeypatch, global_path)

    selections: list[list[str]] = []
    calls = {"count": 0}

    def _fake_select(options, _title):
        selections.append([opt.description or "" for opt in options])
        calls["count"] += 1
        if calls["count"] == 1:
            return config_cmd.AvailableProviders.OPENAI
        return "Continue"

    monkeypatch.setattr(config_cmd, "_select_option", _fake_select)
    monkeypatch.setattr(config_cmd, "secret_prompt", lambda _prompt: "key-123")

    assert config_cmd._configure_provider_keys(global_path) is True
    assert read_env_value(global_path, "OPENAI_API_KEY") == "key-123"
    assert any("API key set" in desc for desc in selections[-1])


def test_edit_entry_saves_and_reports(capsys, tmp_path, monkeypatch) -> None:
    entry = config_cmd.ConfigEntry(
        key="ai_max_context_chars",
        value="1000",
        editable=True,
        source="global",
        description="Max chars sent to AI context",
        category="AI limits",
        env_key="AI_MAX_CONTEXT_CHARS",
        min_value=1000,
    )
    global_path = tmp_path / "global.env"
    global_path.write_text("")

    monkeypatch.setattr(config_cmd, "numeric_input", lambda **_k: 2000)
    monkeypatch.setattr(config_cmd, "modal_confirm", lambda **_k: True)

    config_cmd._edit_entry(entry, global_path)
    output = capsys.readouterr().out
    assert "updated" in output.lower()
    assert read_env_value(global_path, "AI_MAX_CONTEXT_CHARS") == "2000"


def test_select_model_persists_value(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"
    global_path.write_text("")
    set_env_value(global_path, "AI_PROVIDER", "google")
    set_env_value(global_path, "GOOGLE_API_KEY", "key")

    _patch_paths(monkeypatch, global_path)
    _patch_needs_init(monkeypatch, False)
    monkeypatch.setattr(config_cmd, "_run_init_flow", lambda _path: None)

    captured: dict[str, list[str]] = {"models": []}

    def _fake_list_models(_self, _provider, _api_key):
        return ["m1", "m2"]

    def _fake_select(models, _current, on_select, **_kwargs):
        captured["models"] = list(models)
        on_select("m2")

    monkeypatch.setattr(config_cmd.ModelCatalog, "list_models", _fake_list_models)
    monkeypatch.setattr(config_cmd, "interactive_model_select", _fake_select)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "--select-model"])

    assert result.exit_code == 0
    assert captured["models"] == ["m1", "m2"]
    assert read_env_value(global_path, "AI_MODEL") == "m2"


def test_model_catalog_used_for_init(monkeypatch) -> None:
    captured: list[str] = []

    def _fake_list_models(_self, _provider, _api_key):
        return ["m1", "m2"]

    def _fake_select(options, title=None, **_kwargs):
        captured.extend([opt.value for opt in options])
        return "m2"

    monkeypatch.setattr(config_cmd.ModelCatalog, "list_models", _fake_list_models)
    monkeypatch.setattr(config_cmd, "select", _fake_select)
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
