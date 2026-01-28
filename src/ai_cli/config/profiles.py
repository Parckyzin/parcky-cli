from __future__ import annotations

import json
import os
from typing import Any

from ai_cli.config import paths
from ai_cli.core.exceptions import ConfigurationError


def load_profiles() -> dict[str, dict[str, str]]:
    """
    Load profiles from JSON files.

    Priority:
    - Local (./ai-profiles.json) overrides Global (~/.config/ai-cli/ai-profiles.json)
    """
    profiles: dict[str, dict[str, str]] = {}

    # Load global first, then local to override (explicitly documented)
    for path in (paths.get_global_profiles_path(), paths.get_local_profiles_path()):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        if isinstance(data, dict):
            profiles.update(_normalize_profiles(data))

    return profiles


def resolve_profile(profile_name: str) -> dict[str, str]:
    """Resolve a profile by name, raising if missing."""
    profiles = load_profiles()
    if profile_name not in profiles:
        raise ConfigurationError(
            f"Profile '{profile_name}' not found.",
            user_message=(
                f"AI_PROFILE '{profile_name}' was not found. "
                "Check your ai-profiles.json."
            ),
        )
    return profiles[profile_name]


def apply_profile_overrides(
    values: dict[str, Any], profile_name: str
) -> dict[str, Any]:
    """
    Apply profile overrides without overriding already-defined values.

    Note: already-defined includes values from os.environ and dotenv sources.
    """
    overrides = resolve_profile(profile_name)
    merged: dict[str, Any] = dict(values)

    for key, raw_value in overrides.items():
        normalized_key = key.upper()

        if _has_value(merged.get(normalized_key)):
            continue

        resolved = _resolve_env_reference(
            raw_value, profile_name=profile_name, key=normalized_key
        )
        merged[normalized_key] = resolved

    return merged


def _normalize_profiles(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    profiles: dict[str, dict[str, str]] = {}
    for name, values in data.items():
        if not isinstance(values, dict):
            continue
        normalized: dict[str, str] = {}
        for k, v in values.items():
            if not isinstance(k, str):
                continue
            normalized[k.upper()] = str(v)
        profiles[str(name)] = normalized
    return profiles


def _resolve_env_reference(value: str, *, profile_name: str, key: str) -> str:
    value = str(value)
    if value.startswith("env:"):
        env_key = value[4:].strip()
        if not env_key:
            raise ConfigurationError(
                f"Invalid env reference for {key} in profile '{profile_name}'.",
                user_message=f"Profile '{profile_name}' has an invalid env reference for {key}.",
            )

        env_val = os.environ.get(env_key)
        if not _has_value(env_val):
            raise ConfigurationError(
                f"Missing env var '{env_key}' required by profile '{profile_name}' ({key}).",
                user_message=(
                    f"Profile '{profile_name}' requires environment variable '{env_key}' "
                    f"for {key}, but it is not set."
                ),
            )
        return env_val

    return value


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    return str(value).strip() != ""
