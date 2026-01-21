"""CLI entry point wrapper."""

from .app import app


def main() -> None:
    """Run the CLI app."""
    app()


if __name__ == "__main__":
    main()
