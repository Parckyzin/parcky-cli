from __future__ import annotations

from typing import Callable

from ai_cli.clients.anthropic import AnthropicAIService
from ai_cli.clients.gemini import GeminiAIService
from ai_cli.clients.local import LocalAIService
from ai_cli.clients.openai import OpenAIAIService
from ai_cli.config.settings import AIConfig
from ai_cli.core.common.enums import AvailableProviders
from ai_cli.core.exceptions import ConfigurationError
from ai_cli.core.interfaces import AIServiceInterface

_REGISTRY: dict[AvailableProviders, Callable[[AIConfig], AIServiceInterface]] = {
    AvailableProviders.GOOGLE: GeminiAIService,
    AvailableProviders.OPENAI: OpenAIAIService,
    AvailableProviders.ANTHROPIC: AnthropicAIService,
    AvailableProviders.LOCAL: LocalAIService,
}


def get_ai_service(config: AIConfig) -> AIServiceInterface:
    """Factory function to get the appropriate AI service based on configuration."""
    provider = getattr(config, "effective_provider", None)
    if not provider:
        provider = (
            getattr(config, "ai_provider", None)
            or getattr(config, "ai_host", None)
            or config.model_host
        )

    if provider not in _REGISTRY:
        raise ConfigurationError(
            f"Unsupported AI host: {provider}",
            user_message=(
                f"AI_HOST '{provider}' is not supported. "
                "Choose google, openai, anthropic, or local."
            ),
        )

    if (
        provider
        in {
            AvailableProviders.GOOGLE,
            AvailableProviders.OPENAI,
            AvailableProviders.ANTHROPIC,
        }
        and not config.api_key
    ):
        raise ConfigurationError(
            "AI_API_KEY is required for the selected AI provider.",
            user_message="AI_API_KEY is required for the selected provider.",
        )

    if provider == AvailableProviders.LOCAL and not config.base_url:
        raise ConfigurationError(
            "AI_BASE_URL is required for local AI providers.",
            user_message="AI_BASE_URL is required when AI_HOST=local.",
        )

    return _REGISTRY[provider](config)


__all__ = ["get_ai_service"]
