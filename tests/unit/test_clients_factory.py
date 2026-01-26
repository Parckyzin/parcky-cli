"""
Unit tests for AI service factory.
"""

from types import SimpleNamespace

import pytest

from ai_cli.clients import get_ai_service
from ai_cli.clients.anthropic import AnthropicAIService
from ai_cli.clients.gemini import GeminiAIService
from ai_cli.clients.local import LocalAIService
from ai_cli.clients.openai import OpenAIAIService
from ai_cli.config.settings import AIConfig
from ai_cli.core.common.enums import AvailableProviders
from ai_cli.core.exceptions import ConfigurationError


def _config(host: AvailableProviders) -> AIConfig:
    return AIConfig(
        model_host=host,
        model_name="test-model",
        api_key="test-key",
        base_url="http://localhost:11434",
    )


def test_get_ai_service_google():
    config = _config(AvailableProviders.GOOGLE)
    assert isinstance(get_ai_service(config), GeminiAIService)


def test_get_ai_service_openai():
    config = _config(AvailableProviders.OPENAI)
    assert isinstance(get_ai_service(config), OpenAIAIService)


def test_get_ai_service_anthropic():
    config = _config(AvailableProviders.ANTHROPIC)
    assert isinstance(get_ai_service(config), AnthropicAIService)


def test_get_ai_service_local():
    config = _config(AvailableProviders.LOCAL)
    assert isinstance(get_ai_service(config), LocalAIService)


def test_get_ai_service_unknown_host():
    config = SimpleNamespace(model_host="unknown", api_key="x", base_url=None)
    with pytest.raises(ConfigurationError):
        get_ai_service(config)


def test_get_ai_service_requires_api_key():
    config = SimpleNamespace(
        model_host=AvailableProviders.OPENAI, api_key=None, base_url=None
    )
    with pytest.raises(ConfigurationError):
        get_ai_service(config)


def test_get_ai_service_requires_base_url_for_local():
    config = SimpleNamespace(
        model_host=AvailableProviders.LOCAL, api_key=None, base_url=None
    )
    with pytest.raises(ConfigurationError):
        get_ai_service(config)
