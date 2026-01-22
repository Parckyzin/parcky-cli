from pathlib import Path


def get_config_dir() -> Path:
    """Return the global config directory path."""
    return Path.home() / ".config" / "ai-cli"


def get_global_env_path() -> Path:
    """Return the global .env path."""
    return get_config_dir() / ".env"


def get_local_env_path() -> Path:
    """Return the local .env path in the current working directory."""
    return Path.cwd() / ".env"


def get_cache_path() -> Path:
    """Return the cache file path."""
    return get_config_dir() / "cache.json"


def get_global_prompts_path() -> Path:
    """Return the global prompts.json path."""
    return get_config_dir() / "prompts.json"


def get_local_prompts_path() -> Path:
    """Return the local prompts.json path."""
    return Path.cwd() / "prompts.json"


def get_package_prompts_path() -> Path:
    """Return the package prompts.json path."""
    return Path(__file__).resolve().parents[3] / "prompts.json"


def get_local_profiles_path() -> Path:
    """Return the local AI profiles path."""
    return Path.cwd() / "ai-profiles.json"


def get_global_profiles_path() -> Path:
    """Return the global AI profiles path."""
    return get_config_dir() / "ai-profiles.json"
