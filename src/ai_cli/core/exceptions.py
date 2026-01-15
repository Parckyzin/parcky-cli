"""
Custom exceptions for AI CLI application.
"""


class AICliError(Exception):
    """Base exception for AI CLI application."""

    pass


class GitError(AICliError):
    """Exception for git-related errors."""

    pass


class NoStagedChangesError(GitError):
    """Exception when no staged changes are found."""

    pass


class AIServiceError(AICliError):
    """Exception for AI service errors."""

    pass


class ConfigurationError(AICliError):
    """Exception for configuration errors."""

    pass


class PullRequestError(AICliError):
    """Exception for pull request errors."""

    pass


class RepositoryError(AICliError):
    """Exception for repository creation errors."""

    pass
