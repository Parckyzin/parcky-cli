from pathlib import Path

from ai_cli.config.writer import read_ai_provider, read_env_value, set_ai_provider


def test_read_ai_provider_prefers_ai_provider(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text('AI_PROVIDER="openai"\nAI_HOST="google"\n')

    assert read_ai_provider(env_path) == "openai"


def test_read_ai_provider_falls_back_to_ai_host(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text('AI_HOST="local"\n')

    assert read_ai_provider(env_path) == "local"


def test_set_ai_provider_writes_ai_provider(tmp_path: Path):
    env_path = tmp_path / ".env"

    set_ai_provider(env_path, "openai")

    assert read_env_value(env_path, "AI_PROVIDER") == "openai"
