"""
CLI app registration tests.
"""

from typer.testing import CliRunner

from ai_cli.cli.main import app


def _command_name(command) -> str:
    if command.name:
        return command.name
    return command.callback.__name__.replace("_", "-")


def test_cli_commands_registered():
    command_names = {_command_name(command) for command in app.registered_commands}
    expected = {
        "smart-commit",
        "smart-commit-all",
        "create-pr",
        "create-repo",
        "setup",
        "config",
        "version",
    }
    assert expected.issubset(command_names)


def test_config_help_includes_edit_flag():
    runner = CliRunner()
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    output = _strip_ansi(result.output)
    assert "-e" in output
    assert "--edit" in output
    assert "init" in output


def _strip_ansi(value: str) -> str:
    cleaned = value.replace("\x1b", "")
    while True:
        start = cleaned.find("[")
        end = cleaned.find("m", start)
        if start == -1 or end == -1:
            break
        cleaned = cleaned[:start] + cleaned[end + 1 :]
    return cleaned
