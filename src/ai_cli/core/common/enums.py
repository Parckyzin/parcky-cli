from enum import StrEnum


class RepositoryVisibility(StrEnum):
    """Repository visibility options."""

    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class CommitType(StrEnum):
    """Conventional commit types."""

    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    TEST = "test"
    CHORE = "chore"
    BUILD = "build"
    CI = "ci"
    PERF = "perf"
    REVERT = "revert"


class AvailableAiHosts(StrEnum):
    """Available AI service hosts."""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    GOOGLE = "google"
    LOCAL = "local"
