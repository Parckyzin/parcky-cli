# Development

## Local Setup

Use `uv` for dependency management.

```bash
uv sync --group dev
```

## Quality Checks

Run lint and tests:

```bash
task lint
task test
```

Build package:

```bash
uv build
```

## CI

CI runs on GitHub Actions for PRs and pushes to `master`:

- `uv sync --group dev --frozen`
- `uv build`
- `uv run task lint`
- `uv run task test`

## Testing Guidance

- Prefer unit tests for services, pipelines, and config.
- Mock infrastructure and AI providers.
- Avoid network calls in tests.
