from __future__ import annotations

from typing import Protocol

from ai_cli.core.common.enums import AvailableProviders


class ModelCatalogInterface(Protocol):
    """Minimal interface for listing models by provider."""

    def list_models(
        self,
        provider: AvailableProviders,
        api_key: str | None,
    ) -> list[str]:
        """Return a list of model names for a provider."""
