import typer

from .handlers import config_cmd, create_pr, create_repo, smart_commit, smart_commit_all


def create_app() -> typer.Typer:
    """Create the CLI application."""
    app = typer.Typer(
        name="ai-cli",
        help="AI-powered git commit and PR creation tool",
        rich_markup_mode="rich",
    )

    smart_commit.register(app)
    smart_commit_all.register(app)
    create_pr.register(app)
    create_repo.register(app)
    config_cmd.register(app)

    return app


app = create_app()
