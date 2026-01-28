from __future__ import annotations

from ai_cli.clients.gemini import GeminiAIService
from ai_cli.config.settings import AIConfig
from ai_cli.core.common.enums import AvailableProviders
from ai_cli.core.exceptions import AIServiceError, ConfigurationError
from ai_cli.core.interfaces import ModelCatalogInterface


class ModelCatalog(ModelCatalogInterface):
    """List models by provider using provider-specific integrations."""

    def list_models(
        self,
        provider: AvailableProviders,
        api_key: str | None,
    ) -> list[str]:
        if provider.needs_api_key() and not api_key:
            raise ConfigurationError(
                "API key is required to list models.",
                user_message=(
                    f"No API key set for {provider.value}. "
                    "Add one to list models."
                ),
            )

        if provider == AvailableProviders.LOCAL:
            return ["local"]

        if provider == AvailableProviders.GOOGLE:
            config = AIConfig(
                model_host=AvailableProviders.GOOGLE,
                api_key=api_key,
                model_name="gemini-2.0-flash",
            )
            return GeminiAIService(config).get_available_models()

        raise AIServiceError(
            f"Model listing not implemented for {provider.value}.",
            user_message=(
                f"Model listing not implemented for {provider.value}."
            ),
        )
