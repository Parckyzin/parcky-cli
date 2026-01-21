"""
Custom exceptions for AI CLI application.
"""


class ExitCode:
    """Exit code definitions for CLI."""

    SUCCESS = 0
    INTERNAL_ERROR = 1
    USAGE_ERROR = 2
    EXTERNAL_ERROR = 3


class AICliError(Exception):
    """Base exception for AI CLI application."""

    exit_code = ExitCode.INTERNAL_ERROR

    def __init__(
        self,
        message: str,
        *,
        user_message: str | None = None,
        exit_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.user_message: str = user_message or message
        self.exit_code: int = exit_code if exit_code is not None else self.exit_code


class UsageError(AICliError):
    """Exception for invalid usage or user input."""

    exit_code = ExitCode.USAGE_ERROR


class ConfigurationError(UsageError):
    """Exception for configuration errors."""


class ExternalServiceError(AICliError):
    """Exception for external dependency failures."""

    exit_code = ExitCode.EXTERNAL_ERROR


class GitError(ExternalServiceError):
    """Exception for git-related errors."""


class NoStagedChangesError(GitError):
    """Exception when no staged changes are found."""

    exit_code = ExitCode.USAGE_ERROR


class AIServiceError(ExternalServiceError):
    """Exception for AI service errors."""


class PullRequestError(ExternalServiceError):
    """Exception for pull request errors."""


class RepositoryError(ExternalServiceError):
    """Exception for repository creation errors."""
