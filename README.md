# parcky-cli

CLI for AI‑assisted git commits and pull requests with a clean architecture and deterministic context handling.

## What it is

parcky-cli helps you generate commit messages, group commits, and draft PRs using AI providers, while keeping control of diffs, truncation, and prompts.

## Key Features

- Smart commit message generation from staged diffs.
- Deterministic multi‑commit grouping (`smart-commit-all`) with dry‑run and explain mode.
- PR title/body generation with structured context and safe truncation.
- Interactive provider and model selection.
- Config profiles and local/global `.env` configuration.
- GitHub integration via `gh` for PRs and repo creation.

## Installation

Recommended (uv):

Not cloning

```bash
uv tool install parcky-cli
```

Cloning repo:
```bash
uv sync
```

Editable install (for development):

```bash
uv pip install -e .
```

Optional TUI extras (for prompt_toolkit UI):

```bash
uv sync --group dev
```

## Quick Start

Set API key (global):

```bash
parcky-cli setup
```

Select provider and model:

```bash
parcky-cli config --provider
parcky-cli config --select
```

Generate a commit message:

```bash
parcky-cli smart-commit
```

Group and commit all changes:

```bash
parcky-cli smart-commit-all --dry-run
parcky-cli smart-commit-all --yes
```

Create a PR description:

```bash
parcky-cli create-pr
```

Create a GitHub repo (requires `gh`):

```bash
parcky-cli create-repo my-repo --visibility private
```

## Configuration (Basics)

Config is loaded with precedence:

1. `os.environ`
2. Local `.env`
3. Global `~/.config/ai-cli/.env`
4. Defaults

Key settings:

- `AI_PROVIDER` (or legacy `AI_HOST`)
- `AI_MODEL`
- `AI_API_KEY`
- `AI_BASE_URL`
- `AI_MAX_CONTEXT_CHARS`
- `GIT_MAX_DIFF_SIZE`

Interactive config:

```bash
parcky-cli config
parcky-cli config --provider
parcky-cli config --select
```

## GitHub Integration

Commands that interact with GitHub (`create-pr`, `create-repo`) use the GitHub CLI.

Make sure `gh` is installed and authenticated:

```bash
gh auth login
```

## CI and Quality

CI runs on GitHub Actions for PRs and pushes to `master`:

- `uv sync --group dev --frozen`
- `uv build`
- `uv run task lint`
- `uv run task test`

## Documentation

Advanced docs live in `docs/`:

- `docs/architecture.md`
- `docs/cli.md`
- `docs/configuration.md`
- `docs/pipelines.md`
- `docs/development.md`
