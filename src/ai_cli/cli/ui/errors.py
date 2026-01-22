from __future__ import annotations

import typer

from ai_cli.core.exceptions import AICliError, ExitCode

from .console import console


def render_error(error: AICliError, *, debug: bool) -> None:
    """Render a user-friendly error message."""
    console.print(f"[bold red]❌ {error.user_message}[/bold red]")
    if debug and str(error) != error.user_message:
        console.print(f"[dim]Details:[/dim] {error}")


def exit_with_error(error: AICliError, *, debug: bool) -> None:
    """Exit with a domain error."""
    render_error(error, debug=debug)
    raise typer.Exit(error.exit_code) from None


def exit_with_unexpected_error(_error: Exception, *, debug: bool) -> None:
    """Exit with an unexpected error."""
    console.print(
        "[bold red]❌ Unexpected error.[/bold red] "
        "Try again or run with DEBUG=true for details."
    )
    if debug:
        import traceback

        console.print("[dim]Debug traceback:[/dim]")
        console.print(traceback.format_exc())
    raise typer.Exit(ExitCode.INTERNAL_ERROR) from None
