# CLI Flows

This document describes the main CLI flows and how they map to services and pipelines.

## smart-commit

**Goal**: Generate a commit message based on staged changes.

Flow:
1. CLI gathers user input/flags.
2. `SmartCommitService` loads staged diff via `GitRepository`.
3. Pipeline builds a structured AI context (truncation and examples).
4. AI service generates commit message.
5. CLI shows preview, asks for confirmation, then commits (and optionally pushes).

Key points:
- Truncation/summary logic lives in pipelines.
- CLI never formats AI context; it only renders output.

## smart-commit-all

**Goal**: Group changes into multiple commits deterministically.

Flow:
1. CLI forwards options (`--dry-run`, `--explain`, `--push`, `--yes`).
2. `SmartCommitAllService` groups files deterministically.
3. CLI renders groups; in dry-run, no git changes occur.
4. If confirmed, commits and optional push happen via infrastructure.

Key points:
- Grouping logic lives in services/pipelines.
- CLI only renders the grouping and asks for confirmation.

## create-pr

**Goal**: Generate a PR title/body based on branch changes.

Flow:
1. CLI determines base/current branch and calls `CreatePRService`.
2. Git repository provides commits, file stats, and diff excerpts.
3. Pipeline builds a `PRContext` and LLM input text.
4. AI generates PR title/body; fallback is used on AI failure.
5. CLI previews PR and optionally opens it via GitHub CLI service.

Key points:
- PRContext is authoritative; avoid ad-hoc text formatting outside pipelines.
- AI failures must not break the flow.
