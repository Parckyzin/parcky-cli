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


class AvailableProviders(StrEnum):
    """Available AI providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"

    def needs_api_key(self) -> bool:
        """Determine if the provider requires an API key."""
        return self not in {
            AvailableProviders.LOCAL,
        }

    def env_api_key_name(self) -> str:
        """Return the provider-specific API key env var name."""
        return f"{self.value.upper()}_API_KEY"
