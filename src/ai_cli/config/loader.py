from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ai_cli.config import paths
from ai_cli.config.profiles import apply_profile_overrides
from ai_cli.config.writer import read_env_file
from ai_cli.core.common.enums import AvailableProviders
from ai_cli.core.exceptions import ConfigurationError


def get_env_paths() -> tuple[Path, Path]:
    """Return local and global env paths."""
    return paths.get_local_env_path(), paths.get_global_env_path()


def load_dotenv_values() -> dict[str, str]:
    """Load values from global and local .env files with correct precedence."""
    local_path, global_path = get_env_paths()
    values: dict[str, str] = {}
    if global_path.exists():
        values.update(read_env_file(global_path))
    if local_path.exists():
        values.update(read_env_file(local_path))
    return values


def load_settings_values() -> dict[str, str]:
    """Load settings with precedence: env > local .env > global .env."""
    values = load_dotenv_values()
    values.update(dict(os.environ))
    return values


def resolve_setting_source(
    keys: list[str],
    local_path: Path,
    global_path: Path,
) -> str:
    """Resolve the origin of a setting key with precedence env > local > global."""
    upper_keys = {key.upper() for key in keys}
    if any(key in os.environ for key in upper_keys):
        return "env"
    if local_path.exists():
        local_values = read_env_file(local_path)
        if any(key in local_values for key in upper_keys):
            return "local"
    if global_path.exists():
        global_values = read_env_file(global_path)
        if any(key in global_values for key in upper_keys):
            return "global"
    return "default"


def build_settings_dict(values: dict[str, str] | None = None) -> dict[str, Any]:
    """Build settings dict with nested AI/Git structures."""
    raw_env = values or load_settings_values()
    normalized: dict[str, Any] = {str(k).upper(): v for k, v in raw_env.items()}

    def _clean(value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    def _parse_bool(value: str) -> bool:
        v = value.strip().lower()
        if v in {"1", "true", "yes", "y", "on"}:
            return True
        if v in {"0", "false", "no", "n", "off"}:
            return False
        raise ConfigurationError(
            f"Invalid boolean value: {value!r}",
            user_message=f"Invalid boolean value: {value}. Use true/false.",
        )

    def _parse_int(value: str) -> int:
        try:
            return int(value.strip())
        except ValueError as e:
            raise ConfigurationError(
                f"Invalid integer value: {value!r}",
                user_message=f"Invalid number: {value}.",
            ) from e

    def _parse_float(value: str) -> float:
        try:
            return float(value.strip())
        except ValueError as e:
            raise ConfigurationError(
                f"Invalid float value: {value!r}",
                user_message=f"Invalid number: {value}.",
            ) from e

    profile_name = _clean(normalized.get("AI_PROFILE"))
    if profile_name:
        normalized = apply_profile_overrides(normalized, profile_name)

    ai_provider_raw = _clean(normalized.get("AI_PROVIDER"))
    ai_host_raw = _clean(normalized.get("AI_HOST"))
    ai_provider_value = ai_provider_raw or ai_host_raw
    ai_host_value = (ai_provider_value or AvailableProviders.GOOGLE.value).lower()

    ai_model_value = _clean(normalized.get("AI_MODEL")) or _clean(
        normalized.get("MODEL_NAME")
    )

    ai_api_key_value = _clean(normalized.get("AI_API_KEY"))
    if not ai_api_key_value and ai_host_value == AvailableProviders.GOOGLE.value:
        ai_api_key_value = _clean(normalized.get("GEMINI_API_KEY"))

    ai_values: dict[str, Any] = {"model_host": ai_host_value}
    if ai_provider_raw is not None:
        ai_values["ai_provider"] = ai_provider_raw
    if ai_host_raw is not None:
        ai_values["ai_host"] = ai_host_raw

    if ai_model_value:
        ai_values["model_name"] = ai_model_value
    if ai_api_key_value:
        ai_values["api_key"] = ai_api_key_value

    base_url = _clean(normalized.get("AI_BASE_URL"))
    if base_url is not None:
        ai_values["base_url"] = base_url

    temperature = _clean(normalized.get("AI_TEMPERATURE"))
    if temperature is not None:
        ai_values["temperature"] = _parse_float(temperature)

    max_tokens = _clean(normalized.get("AI_MAX_TOKENS"))
    if max_tokens is not None:
        ai_values["max_tokens"] = _parse_int(max_tokens)

    cache_enabled = _clean(normalized.get("AI_CACHE_ENABLED"))
    if cache_enabled is not None:
        ai_values["cache_enabled"] = _parse_bool(cache_enabled)

    max_context_chars = _clean(normalized.get("AI_MAX_CONTEXT_CHARS"))
    if max_context_chars is not None:
        ai_values["max_context_chars"] = _parse_int(max_context_chars)

    system_instruction = _clean(normalized.get("AI_SYSTEM_INSTRUCTION"))
    if system_instruction is not None:
        ai_values["system_instruction"] = system_instruction

    git_values: dict[str, Any] = {}

    git_max_diff_size = _clean(normalized.get("GIT_MAX_DIFF_SIZE"))
    if git_max_diff_size is not None:
        git_values["max_diff_size"] = _parse_int(git_max_diff_size)

    git_default_branch = _clean(normalized.get("GIT_DEFAULT_BRANCH"))
    if git_default_branch is not None:
        git_values["default_branch"] = git_default_branch

    git_auto_push = _clean(normalized.get("GIT_AUTO_PUSH"))
    if git_auto_push is not None:
        git_values["auto_push"] = _parse_bool(git_auto_push)

    settings: dict[str, Any] = {}

    debug_value = _clean(normalized.get("DEBUG"))
    if debug_value is not None:
        settings["debug"] = _parse_bool(debug_value)

    log_level_value = _clean(normalized.get("LOG_LEVEL"))
    if log_level_value is not None:
        settings["log_level"] = log_level_value

    settings["ai"] = ai_values
    if git_values:
        settings["git"] = git_values

    return settings
