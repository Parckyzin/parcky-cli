# Configuration

Configuration is loaded from environment variables and `.env` files with a strict precedence:

1. `os.environ`
2. Local `.env` in the repository
3. Global `.env` at `~/.config/ai-cli/.env`
4. Defaults

All reads and writes must use helpers in `config/paths.py`, `config/loader.py`, and `config/writer.py`.

## Provider and Model Settings

- `AI_PROVIDER`: active provider (new key).
- `AI_HOST`: legacy alias for provider; still accepted.
- `AI_MODEL`: model name (provider-specific).
- `AI_API_KEY`: API key for the active provider.
- `AI_BASE_URL`: base URL for local/self-hosted providers.

Legacy aliases:
- `MODEL_NAME` is accepted as alias for `AI_MODEL`.
- `GEMINI_API_KEY` is accepted when provider is Google/Gemini.

## Profiles

- `AI_PROFILE` selects a named profile.
- Profile JSON locations (priority):
  - `./ai-profiles.json`
  - `~/.config/ai-cli/ai-profiles.json`
- Profile values can reference secrets using `env:VAR_NAME`.

Profiles act as overrides below env/local/global, but do not override values already set in env files or `os.environ`.

## Key Settings (MVP)

- `AI_MAX_CONTEXT_CHARS`: hard limit for AI context size.
- `GIT_MAX_DIFF_SIZE`: maximum diff size passed to AI.
- `AI_SYSTEM_INSTRUCTION`: optional system prompt override.

## CLI Configuration UX

The `config` command supports:
- interactive model selection (with provider switching),
- interactive provider selection,
- editing specific numeric settings with validation.

UI changes are persisted via `config/writer.py`.
