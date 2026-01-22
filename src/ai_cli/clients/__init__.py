from __future__ import annotations

from typing import Callable

from ai_cli.clients.anthropic import AnthropicAIService
from ai_cli.clients.gemini import GeminiAIService
from ai_cli.clients.local import LocalAIService
from ai_cli.clients.openai import OpenAIAIService
from ai_cli.config.settings import AIConfig
from ai_cli.core.common.enums import AvailableAiHosts
from ai_cli.core.exceptions import ConfigurationError
from ai_cli.core.interfaces import AIServiceInterface

_REGISTRY: dict[AvailableAiHosts, Callable[[AIConfig], AIServiceInterface]] = {
    AvailableAiHosts.GOOGLE: GeminiAIService,
    AvailableAiHosts.OPENAI: OpenAIAIService,
    AvailableAiHosts.ANTHROPIC: AnthropicAIService,
    AvailableAiHosts.LOCAL: LocalAIService,
}


def get_ai_service(config: AIConfig) -> AIServiceInterface:
    """Factory function to get the appropriate AI service based on configuration."""
    if config.model_host not in _REGISTRY:
        raise ConfigurationError(
            f"Unsupported AI host: {config.model_host}",
            user_message=(
                f"AI_HOST '{config.model_host}' is not supported. "
                "Choose google, openai, anthropic, or local."
            ),
        )

    if config.model_host in {
        AvailableAiHosts.GOOGLE,
        AvailableAiHosts.OPENAI,
        AvailableAiHosts.ANTHROPIC,
    } and not config.api_key:
        raise ConfigurationError(
            "AI_API_KEY is required for the selected AI provider.",
            user_message="AI_API_KEY is required for the selected provider.",
        )

    if config.model_host == AvailableAiHosts.LOCAL and not config.base_url:
        raise ConfigurationError(
            "AI_BASE_URL is required for local AI providers.",
            user_message="AI_BASE_URL is required when AI_HOST=local.",
        )

    return _REGISTRY[config.model_host](config)


__all__ = ["get_ai_service"]
