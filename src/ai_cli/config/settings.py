"""
Configuration management for AI CLI application using pydantic-settings.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..core.exceptions import ConfigurationError


def get_env_files() -> list[Path]:
    """Get list of .env files to load, in order of priority."""
    env_files = []

    local_env = Path(".env")
    if local_env.exists():
        env_files.append(local_env)

    global_env = Path.home() / ".config" / "ai-cli" / ".env"
    if global_env.exists():
        env_files.append(global_env)

    return env_files if env_files else [Path(".env")]


class AIConfig(BaseSettings):
    """AI service configuration."""

    model_config = SettingsConfigDict(
        env_file=get_env_files(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    api_key: str = Field(
        ..., description="Google Gemini API key", validation_alias="GEMINI_API_KEY"
    )
    model_name: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model to use",
        validation_alias="MODEL_NAME",
    )
    system_instruction: str = Field(
        default="You are a senior DevOps engineer obsessed with best practices and Conventional Commits.",
        description="AI system instruction",
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens for AI response"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="AI temperature (0.0-2.0)"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v or not v.strip():
            raise ConfigurationError("GEMINI_API_KEY is required and cannot be empty")
        return v.strip()


class GitConfig(BaseSettings):
    """Git configuration."""

    model_config = SettingsConfigDict(
        env_prefix="GIT_",
        env_file=get_env_files(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    max_diff_size: int = Field(
        default=10000, gt=0, description="Maximum diff size for AI analysis"
    )
    default_branch: str = Field(default="main", description="Default git branch name")
    auto_push: bool = Field(default=True, description="Auto push commits by default")

    @field_validator("default_branch")
    @classmethod
    def validate_branch_name(cls, v):
        if not v or not v.strip():
            raise ConfigurationError("Default branch name cannot be empty")
        return v.strip()


class AppConfig(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Nested configurations
    ai: AIConfig = Field(default_factory=AIConfig)
    git: GitConfig = Field(default_factory=GitConfig)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ConfigurationError(
                f"Invalid log level: {v}. Must be one of {valid_levels}"
            )
        return v.upper()

    def __init__(self, **kwargs):
        """Initialize configuration with proper error handling."""
        try:
            super().__init__(**kwargs)
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration with error handling."""
        try:
            return cls()
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load application configuration: {e}"
            ) from e

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return self.model_dump()

    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug
