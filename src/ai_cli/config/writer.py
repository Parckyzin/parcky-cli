from pathlib import Path


def read_env_file(path: Path) -> dict[str, str]:
    """Read a .env file into a dict."""
    data: dict[str, str] = {}
    if not path.exists():
        return data
    try:
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            value = _strip_quotes(value.strip())
            data[key.strip()] = value
    except OSError:
        return {}
    return data


def read_env_value(path: Path, key: str) -> str:
    """Read a single value from a .env file."""
    return read_env_file(path).get(key, "")


def read_ai_provider(path: Path) -> str:
    """Read AI provider with fallback to legacy AI_HOST."""
    return read_env_value(path, "AI_PROVIDER") or read_env_value(path, "AI_HOST")


def set_env_value(path: Path, key: str, value: str) -> None:
    """Set or update a .env key in a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if path.exists():
        try:
            lines = path.read_text().splitlines()
        except OSError:
            lines = []

    updated = False
    new_lines: list[str] = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f'{key}="{value}"')
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(f'{key}="{value}"')

    path.write_text("\n".join(new_lines).strip() + "\n")


def set_ai_provider(path: Path, value: str) -> None:
    """Set AI provider in a .env file (new key)."""
    set_env_value(path, "AI_PROVIDER", value)


def set_config_value(path: Path, key: str, value: str | int) -> None:
    """Set a generic config value as a string."""
    set_env_value(path, key, str(value))


def _strip_quotes(value: str) -> str:
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value
