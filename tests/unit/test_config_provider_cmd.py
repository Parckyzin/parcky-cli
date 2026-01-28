from typer.testing import CliRunner

from ai_cli.cli import main as cli_main
from ai_cli.cli.handlers import config_cmd
from ai_cli.config import writer


def test_config_provider_select_persists_and_clears_model(
    tmp_path, monkeypatch
) -> None:
    global_path = tmp_path / "global.env"
    writer.set_env_value(global_path, "AI_MODEL", "old-model")
    writer.set_env_value(global_path, "MODEL_NAME", "legacy-model")
    writer.set_env_value(global_path, "OPENAI_API_KEY", "test-key")

    monkeypatch.setattr(config_cmd, "get_global_env_path", lambda: global_path)
    monkeypatch.setattr(config_cmd, "needs_init", lambda *_a, **_k: False)
    monkeypatch.setattr(
        config_cmd, "prompt_provider_select", lambda **_kwargs: "openai"
    )

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-p"])

    assert result.exit_code == 0
    assert writer.read_env_value(global_path, "AI_PROVIDER") == "openai"
    assert writer.read_env_value(global_path, "AI_MODEL") == ""
    assert writer.read_env_value(global_path, "MODEL_NAME") == ""


def test_config_provider_cancel_does_not_persist(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"

    monkeypatch.setattr(config_cmd, "get_global_env_path", lambda: global_path)
    monkeypatch.setattr(config_cmd, "needs_init", lambda *_a, **_k: False)
    monkeypatch.setattr(config_cmd, "prompt_provider_select", lambda **_kwargs: None)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-p"])

    assert result.exit_code == 0
    assert not global_path.exists()


def test_config_provider_blocks_without_key(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"

    monkeypatch.setattr(config_cmd, "get_global_env_path", lambda: global_path)
    monkeypatch.setattr(config_cmd, "needs_init", lambda *_a, **_k: False)
    monkeypatch.setattr(
        config_cmd, "prompt_provider_select", lambda **_kwargs: "openai"
    )
    monkeypatch.setattr(config_cmd, "confirm", lambda *_args, **_kwargs: False)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-p"])

    assert result.exit_code == 0
    assert writer.read_env_value(global_path, "AI_PROVIDER") == ""


def test_config_provider_adds_key_and_persists(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"

    monkeypatch.setattr(config_cmd, "get_global_env_path", lambda: global_path)
    monkeypatch.setattr(config_cmd, "needs_init", lambda *_a, **_k: False)
    monkeypatch.setattr(
        config_cmd, "prompt_provider_select", lambda **_kwargs: "openai"
    )
    monkeypatch.setattr(config_cmd, "confirm", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(config_cmd, "prompt", lambda _msg: "new-key")

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-p"])

    assert result.exit_code == 0
    assert writer.read_env_value(global_path, "OPENAI_API_KEY") == "new-key"
    assert writer.read_env_value(global_path, "AI_PROVIDER") == "openai"
