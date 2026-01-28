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
    assert "-e" in result.output
    assert "--edit" in result.output
