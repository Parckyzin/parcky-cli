# Pipelines

Pipelines centralize AI-related logic and are the authoritative source of truth for:

- Context construction (commit/PR inputs)
- Truncation and excerpting rules
- Deterministic ordering
- Output formatting requirements

## Why Pipelines Exist

Pipelines prevent drift across services and keep AI prompts consistent. Services call pipelines rather than duplicating context logic.

## Key Pipelines

### Commit Message Pipeline

Responsible for:
- Building a summarized diff context
- Selecting example hunks
- Adding truncation notes

Used by:
- `SmartCommitService`

### PR Context Builder

Responsible for:
- Branch comparison metadata (commits, file stats, rename handling)
- Categorization of files
- Curated patch excerpts for priority files
- Truncation and exclusion notes

Used by:
- `CreatePRService`

## Rules

- Do not format AI context in CLI or services.
- All diff truncation decisions should be in pipelines.
- Any new AI prompt or context rule should be implemented here.
