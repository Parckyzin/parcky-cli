"""
Unit tests for AI profile configuration.
"""

from pathlib import Path

import pytest

from ai_cli.config import paths
from ai_cli.config.settings import AppConfig
from ai_cli.core.common.enums import AvailableProviders
from ai_cli.core.exceptions import ConfigurationError


def _write_profiles(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _set_env_paths(monkeypatch, tmp_path):
    local_env = tmp_path / "local.env"
    global_env = tmp_path / "global.env"
    monkeypatch.setattr(paths, "get_local_env_path", lambda: local_env)
    monkeypatch.setattr(paths, "get_global_env_path", lambda: global_env)


def test_profile_overrides_apply(monkeypatch, tmp_path):
    _set_env_paths(monkeypatch, tmp_path)
    local_profiles = tmp_path / "ai-profiles.json"
    monkeypatch.setattr(paths, "get_local_profiles_path", lambda: local_profiles)
    monkeypatch.setattr(
        paths, "get_global_profiles_path", lambda: tmp_path / "none.json"
    )

    _write_profiles(
        local_profiles,
        '{"team": {"AI_HOST": "openai", "AI_MODEL": "gpt-4o-mini", "AI_API_KEY": "env:OPENAI_KEY"}}',
    )

    monkeypatch.setenv("AI_PROFILE", "team")
    monkeypatch.setenv("OPENAI_KEY", "profile-key")

    config = AppConfig.load()

    assert config.ai.model_host == AvailableProviders.OPENAI
    assert config.ai.model_name == "gpt-4o-mini"
    assert config.ai.api_key == "profile-key"


def test_profile_does_not_override_env(monkeypatch, tmp_path):
    _set_env_paths(monkeypatch, tmp_path)
    local_profiles = tmp_path / "ai-profiles.json"
    monkeypatch.setattr(paths, "get_local_profiles_path", lambda: local_profiles)
    monkeypatch.setattr(
        paths, "get_global_profiles_path", lambda: tmp_path / "none.json"
    )

    _write_profiles(
        local_profiles,
        '{"team": {"AI_MODEL": "profile-model", "AI_API_KEY": "profile-key"}}',
    )

    monkeypatch.setenv("AI_PROFILE", "team")
    monkeypatch.setenv("AI_MODEL", "env-model")
    monkeypatch.setenv("AI_API_KEY", "env-key")

    config = AppConfig.load()

    assert config.ai.model_name == "env-model"
    assert config.ai.api_key == "env-key"


def test_missing_profile_raises(monkeypatch, tmp_path):
    _set_env_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(
        paths, "get_local_profiles_path", lambda: tmp_path / "none.json"
    )
    monkeypatch.setattr(
        paths, "get_global_profiles_path", lambda: tmp_path / "none.json"
    )

    monkeypatch.setenv("AI_PROFILE", "missing")

    with pytest.raises(ConfigurationError):
        AppConfig.load()


def test_env_reference_resolves(monkeypatch, tmp_path):
    _set_env_paths(monkeypatch, tmp_path)
    local_profiles = tmp_path / "ai-profiles.json"
    monkeypatch.setattr(paths, "get_local_profiles_path", lambda: local_profiles)
    monkeypatch.setattr(
        paths, "get_global_profiles_path", lambda: tmp_path / "none.json"
    )

    _write_profiles(
        local_profiles,
        '{"team": {"AI_API_KEY": "env:PROFILE_API_KEY"}}',
    )

    monkeypatch.setenv("AI_PROFILE", "team")
    monkeypatch.setenv("PROFILE_API_KEY", "resolved-key")

    config = AppConfig.load()

    assert config.ai.api_key == "resolved-key"
