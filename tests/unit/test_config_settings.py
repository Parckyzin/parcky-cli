"""
Unit tests for configuration loading and validation.
"""

from pathlib import Path

import pytest

from ai_cli.config import paths
from ai_cli.config.settings import AppConfig
from ai_cli.config.writer import set_env_value
from ai_cli.core.exceptions import ConfigurationError


def _write_env(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for key, value in values.items():
        set_env_value(path, key, value)


def test_env_precedence_env_over_local_and_global(monkeypatch, tmp_path):
    global_env = tmp_path / "global.env"
    local_env = tmp_path / "local.env"

    _write_env(global_env, {"AI_MODEL": "global-model"})
    _write_env(local_env, {"AI_MODEL": "local-model"})

    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_env)
    monkeypatch.setattr(paths, "get_local_env_path", lambda: local_env)
    monkeypatch.setenv("AI_MODEL", "env-model")
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AI_HOST", raising=False)

    config = AppConfig.load()

    assert config.ai.model_name == "env-model"


def test_env_precedence_local_over_global(monkeypatch, tmp_path):
    global_env = tmp_path / "global.env"
    local_env = tmp_path / "local.env"

    _write_env(global_env, {"AI_MODEL": "global-model"})
    _write_env(local_env, {"AI_MODEL": "local-model"})

    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_env)
    monkeypatch.setattr(paths, "get_local_env_path", lambda: local_env)
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AI_HOST", raising=False)

    config = AppConfig.load()

    assert config.ai.model_name == "local-model"


def test_provider_requires_api_key(monkeypatch, tmp_path):
    global_env = tmp_path / "global.env"
    local_env = tmp_path / "local.env"

    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_env)
    monkeypatch.setattr(paths, "get_local_env_path", lambda: local_env)
    monkeypatch.setenv("AI_HOST", "openai")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ConfigurationError):
        AppConfig.load()


def test_local_provider_allows_missing_api_key_but_requires_base_url(
    monkeypatch, tmp_path
):
    global_env = tmp_path / "global.env"
    local_env = tmp_path / "local.env"

    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_env)
    monkeypatch.setattr(paths, "get_local_env_path", lambda: local_env)
    monkeypatch.setenv("AI_HOST", "local")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)

    with pytest.raises(ConfigurationError):
        AppConfig.load()

    monkeypatch.setenv("AI_BASE_URL", "http://localhost:11434")
    config = AppConfig.load()

    assert config.ai.base_url == "http://localhost:11434"


def test_ai_provider_preferred_over_ai_host(monkeypatch, tmp_path):
    global_env = tmp_path / "global.env"
    local_env = tmp_path / "local.env"

    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_env)
    monkeypatch.setattr(paths, "get_local_env_path", lambda: local_env)
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_HOST", "google")
    monkeypatch.setenv("AI_API_KEY", "test-key")

    config = AppConfig.load()

    assert config.ai.ai_provider == "openai"
    assert config.ai.ai_host == "google"
    assert config.ai.effective_provider == "openai"


def test_ai_provider_falls_back_to_ai_host(monkeypatch, tmp_path):
    global_env = tmp_path / "global.env"
    local_env = tmp_path / "local.env"

    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_env)
    monkeypatch.setattr(paths, "get_local_env_path", lambda: local_env)
    monkeypatch.setenv("AI_HOST", "local")
    monkeypatch.setenv("AI_BASE_URL", "http://localhost:11434")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    config = AppConfig.load()

    assert config.ai.ai_provider is None
    assert config.ai.ai_host == "local"
    assert config.ai.effective_provider == "local"
