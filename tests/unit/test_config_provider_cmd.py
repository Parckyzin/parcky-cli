from types import SimpleNamespace

from typer.testing import CliRunner

from ai_cli.cli import main as cli_main
from ai_cli.cli.handlers import config_cmd
from ai_cli.config import writer


def test_config_provider_select_persists_and_clears_model(
    tmp_path, monkeypatch
) -> None:
    local_path = tmp_path / ".env"
    writer.set_env_value(local_path, "AI_MODEL", "old-model")
    writer.set_env_value(local_path, "MODEL_NAME", "legacy-model")

    monkeypatch.setattr(config_cmd, "get_local_env_path", lambda: local_path)
    monkeypatch.setattr(
        config_cmd, "get_global_env_path", lambda: tmp_path / "global.env"
    )
    monkeypatch.setattr(
        config_cmd,
        "get_context",
        lambda: SimpleNamespace(config=SimpleNamespace(debug=False)),
    )
    monkeypatch.setattr(config_cmd, "prompt_provider_select", lambda current: "openai")

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-p"])

    assert result.exit_code == 0
    assert writer.read_env_value(local_path, "AI_PROVIDER") == "openai"
    assert writer.read_env_value(local_path, "AI_MODEL") == ""
    assert writer.read_env_value(local_path, "MODEL_NAME") == ""


def test_config_provider_cancel_does_not_persist(tmp_path, monkeypatch) -> None:
    global_path = tmp_path / "global.env"

    monkeypatch.setattr(config_cmd, "get_local_env_path", lambda: tmp_path / ".env")
    monkeypatch.setattr(config_cmd, "get_global_env_path", lambda: global_path)
    monkeypatch.setattr(
        config_cmd,
        "get_context",
        lambda: SimpleNamespace(config=SimpleNamespace(debug=False)),
    )
    monkeypatch.setattr(config_cmd, "prompt_provider_select", lambda current: None)

    runner = CliRunner()
    result = runner.invoke(cli_main.app, ["config", "-p"])

    assert result.exit_code == 0
    assert not global_path.exists()
