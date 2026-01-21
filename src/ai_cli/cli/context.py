from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

from ai_cli.clients import get_ai_service
from ai_cli.config.cache import get_cache
from ai_cli.config.settings import AppConfig
from ai_cli.core.exceptions import PullRequestError
from ai_cli.core.interfaces import AIServiceInterface
from ai_cli.infrastructure.git_repository import GitRepository
from ai_cli.infrastructure.pr_service import GitHubPRService

from .ui.console import console

if TYPE_CHECKING:
    from ai_cli.config.cache import Cache


@dataclass(frozen=True)
class CLIContext:
    """CLI dependency container."""

    config: AppConfig
    git_repo: GitRepository
    ai_service: AIServiceInterface
    pr_service: GitHubPRService | None
    cache: Cache


@lru_cache(maxsize=1)
def get_context() -> CLIContext:
    """Build and cache CLI dependencies."""
    config = AppConfig.load()
    git_repo = GitRepository(config.git)
    ai_service = get_ai_service(config.ai)
    cache = get_cache()
    pr_service: GitHubPRService | None

    try:
        pr_service = GitHubPRService(work_dir=git_repo.work_dir)
    except PullRequestError as exc:
        if config.debug:
            console.print(f"[yellow]Warning:[/yellow] {exc.user_message}")
            if str(exc) != exc.user_message:
                console.print(f"[dim]Details:[/dim] {exc}")
        pr_service = None

    return CLIContext(
        config=config,
        git_repo=git_repo,
        ai_service=ai_service,
        pr_service=pr_service,
        cache=cache,
    )
