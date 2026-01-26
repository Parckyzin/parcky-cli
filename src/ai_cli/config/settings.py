"""
Configuration management for AI CLI application using pydantic-settings.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from ai_cli.config import loader
from ai_cli.core.common.enums import AvailableProviders
from ai_cli.core.exceptions import ConfigurationError

DEFAULT_SYSTEM_INSTRUCTION = (
    "You are a senior DevOps engineer obsessed with best practices "
    "and Conventional Commits."
)


class AIConfig(BaseModel):
    """AI service configuration."""

    ai_provider: Optional[str] = Field(
        default=None,
        description="Preferred AI provider name (new field, overrides ai_host)",
    )
    ai_host: Optional[str] = Field(
        default=None,
        description="Legacy AI provider name (compatibility field)",
    )
    model_host: AvailableProviders = Field(
        default=AvailableProviders.GOOGLE, description="AI model host service"
    )
    model_name: str = Field(
        default="gemini-2.0-flash",
        description="AI model to use",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for the AI service",
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for the AI service",
    )
    system_instruction: Optional[str] = Field(
        default=None,
        description=("AI system instruction (set via AI_SYSTEM_INSTRUCTION or config)"),
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens for AI response"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="AI temperature (0.0-2.0)"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable AI response cache",
    )
    max_context_chars: int = Field(
        default=35000,
        gt=0,
        description="Maximum context size for AI prompts (characters)",
    )

    @field_validator("ai_provider", "ai_host")
    @classmethod
    def normalize_provider_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized if normalized else None

    @property
    def effective_provider(self) -> Optional[str]:
        """Return the effective AI provider for compatibility checks."""
        return self.ai_provider or self.ai_host

    @model_validator(mode="after")
    def validate_provider_settings(self):
        """Validate provider-specific requirements."""
        if self.model_host in {
            AvailableProviders.GOOGLE,
            AvailableProviders.OPENAI,
            AvailableProviders.ANTHROPIC,
        } and (not self.api_key or not self.api_key.strip()):
            raise ConfigurationError(
                "AI_API_KEY is required for the selected AI provider.",
                user_message=(
                    "AI_API_KEY is required for the selected provider. "
                    "Set AI_API_KEY in your configuration."
                ),
            )
        if self.model_host == AvailableProviders.LOCAL and (
            not self.base_url or not self.base_url.strip()
        ):
            raise ConfigurationError(
                "AI_BASE_URL is required for local AI providers.",
                user_message=(
                    "AI_BASE_URL is required when AI_HOST=local. "
                    "Set AI_BASE_URL in your configuration."
                ),
            )
        if not self.system_instruction or not self.system_instruction.strip():
            from ai_cli.config.prompts import get_prompt

            prompt_value = get_prompt("system_instruction").strip()
            self.system_instruction = prompt_value or DEFAULT_SYSTEM_INSTRUCTION
        return self


class GitConfig(BaseModel):
    """Git configuration."""

    max_diff_size: int = Field(
        default=10000, gt=0, description="Maximum diff size for AI analysis"
    )
    default_branch: str = Field(default="main", description="Default git branch name")
    auto_push: bool = Field(default=True, description="Auto push commits by default")

    @field_validator("default_branch")
    @classmethod
    def validate_branch_name(cls, v):
        if not v or not v.strip():
            raise ConfigurationError(
                "Default branch name cannot be empty",
                user_message=(
                    "Default branch name is empty. Set GIT_DEFAULT_BRANCH or "
                    "update your configuration."
                ),
            )
        return v.strip()


class AppConfig(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Nested configurations
    ai: AIConfig = Field(default_factory=AIConfig)
    git: GitConfig = Field(default_factory=GitConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        _settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Load settings from a single merged source."""

        def _load_settings() -> dict:
            return loader.build_settings_dict()

        return (init_settings, _load_settings)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ConfigurationError(
                f"Invalid log level: {v}. Must be one of {valid_levels}",
                user_message=(
                    "Invalid log level. Use one of: DEBUG, INFO, WARNING, "
                    "ERROR, CRITICAL."
                ),
            )
        return v.upper()

    def __init__(self, **kwargs):
        """Initialize configuration with proper error handling."""
        try:
            super().__init__(**kwargs)
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration: {e}",
                user_message=(
                    "Configuration is invalid. Review your .env files and try again."
                ),
            ) from e

    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration with error handling."""
        try:
            return cls()
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load application configuration: {e}",
                user_message=(
                    "Failed to load configuration. Check your .env files and "
                    "environment variables."
                ),
            ) from e

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return self.model_dump()

    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug
