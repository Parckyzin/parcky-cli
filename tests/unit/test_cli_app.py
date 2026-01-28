"""
CLI app registration tests.
"""

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
