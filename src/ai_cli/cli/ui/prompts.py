import typer
from rich.prompt import Confirm


def confirm(message: str, default: bool = True) -> bool:
    """Render a confirmation prompt."""
    return Confirm.ask(message, default=default)


def prompt(message: str, default: str | None = None) -> str:
    """Render a text prompt."""
    return typer.prompt(message, default=default)
