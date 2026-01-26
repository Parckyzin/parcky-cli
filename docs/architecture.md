# Architecture

parcky-cli follows a layered architecture with strict boundaries. Layers are ordered from outer (UI) to inner (domain).

## Layers and Responsibilities

1. **cli/**
   - Typer commands and Rich rendering only.
   - No business logic or external SDK usage.
   - Delegates to services and renders results/errors.

2. **services/**
   - Orchestrates use cases and workflows.
   - Calls pipelines for AI context and formatting.
   - Calls infrastructure for external interactions (git, AI providers, GitHub CLI).

3. **pipelines/**
   - Source of truth for AI context shaping and generation logic.
   - Defines what is sent to AI, truncation rules, and determinism.

4. **infrastructure/**
   - External integrations: git commands, AI SDKs, GitHub CLI.
   - Implements interfaces from `core/interfaces`.

5. **core/**
   - Domain models, enums, interfaces, exceptions.
   - No dependency on Rich/Typer or external SDKs.

6. **config/**
   - Settings, env loading, cache, prompt templates, and file paths.
   - All env reads/writes should go through loader/writer helpers.

## Dependency Direction

- `cli` depends on `services`, `config`, and `infrastructure` via context.
- `services` depends on `pipelines`, `core`, and `infrastructure`.
- `pipelines` depends on `core` only.
- `infrastructure` depends on `core`.
- `core` depends on nothing else.

## Key Design Decisions

- **Pipelines are the source of truth** for AI context and prompt shaping.
- **CLI is thin**: no business logic; only input/output and user interaction.
- **Error handling is centralized** in `core/exceptions` and rendered in `cli/ui/errors`.

## Diagrams

See `docs/diagrams/workflows.md` for architecture and workflow diagrams.
