from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from . import paths
from .writer import read_env_file
from ..core.common.enums import AvailableAiHosts


def get_env_paths() -> tuple[Path, Path]:
    """Return local and global env paths."""
    return paths.get_local_env_path(), paths.get_global_env_path()


def load_dotenv_values() -> dict[str, str]:
    """Load values from global and local .env files with correct precedence."""
    local_path, global_path = get_env_paths()
    values: dict[str, str] = {}
    values.update(read_env_file(global_path))
    values.update(read_env_file(local_path))
    return values


def load_settings_values() -> dict[str, str]:
    """Load settings with precedence: env > local .env > global .env."""
    values = load_dotenv_values()
    values.update(os.environ)
    return values


def build_settings_dict(values: dict[str, str] | None = None) -> dict[str, Any]:
    """Build settings dict with nested AI/Git structures."""
    env = values or load_settings_values()
    normalized = {k.upper(): v for k, v in env.items()}
    def _clean(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None

    ai_host_value = _clean(normalized.get("AI_HOST"))
    if not ai_host_value:
        ai_host_value = AvailableAiHosts.GOOGLE.value
    else:
        ai_host_value = ai_host_value.lower()

    ai_model_value = _clean(normalized.get("AI_MODEL")) or _clean(
        normalized.get("MODEL_NAME")
    )
    ai_api_key_value = _clean(normalized.get("AI_API_KEY"))
    if not ai_api_key_value and ai_host_value == AvailableAiHosts.GOOGLE.value:
        ai_api_key_value = _clean(normalized.get("GEMINI_API_KEY"))

    ai_values: dict[str, Any] = {}
    if ai_host_value:
        ai_values["model_host"] = ai_host_value
    if ai_model_value:
        ai_values["model_name"] = ai_model_value
    if ai_api_key_value:
        ai_values["api_key"] = ai_api_key_value
    base_url = _clean(normalized.get("AI_BASE_URL"))
    if base_url is not None:
        ai_values["base_url"] = base_url
    temperature = _clean(normalized.get("AI_TEMPERATURE"))
    if temperature is not None:
        ai_values["temperature"] = temperature
    max_tokens = _clean(normalized.get("AI_MAX_TOKENS"))
    if max_tokens is not None:
        ai_values["max_tokens"] = max_tokens
    cache_enabled = _clean(normalized.get("AI_CACHE_ENABLED"))
    if cache_enabled is not None:
        ai_values["cache_enabled"] = cache_enabled
    max_context_chars = _clean(normalized.get("AI_MAX_CONTEXT_CHARS"))
    if max_context_chars is not None:
        ai_values["max_context_chars"] = max_context_chars

    git_values: dict[str, Any] = {}
    git_max_diff_size = _clean(normalized.get("GIT_MAX_DIFF_SIZE"))
    if git_max_diff_size is not None:
        git_values["max_diff_size"] = git_max_diff_size
    git_default_branch = _clean(normalized.get("GIT_DEFAULT_BRANCH"))
    if git_default_branch is not None:
        git_values["default_branch"] = git_default_branch
    git_auto_push = _clean(normalized.get("GIT_AUTO_PUSH"))
    if git_auto_push is not None:
        git_values["auto_push"] = git_auto_push

    settings: dict[str, Any] = {}
    debug_value = _clean(normalized.get("DEBUG"))
    if debug_value is not None:
        settings["debug"] = debug_value
    log_level_value = _clean(normalized.get("LOG_LEVEL"))
    if log_level_value is not None:
        settings["log_level"] = log_level_value
    if ai_values:
        settings["ai"] = ai_values
    if git_values:
        settings["git"] = git_values

    return settings
