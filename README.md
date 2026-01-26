# AI CLI 🤖
**AI-powered Git commits and Pull Requests, done right.**

AI CLI is a command-line tool that uses **Google Gemini** to generate
**high-quality commit messages and Pull Requests** based on your actual
code changes — automatically, consistently, and following best practices.

Spend less time writing commits and PRs. Spend more time coding.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

---

## ✨ What AI CLI does

- 🤖 **Generate Conventional Commit messages** from real diffs
- 📋 **Create Pull Requests automatically**, including:
    - What changed
    - Why it changed
    - How to test
- 🚀 **Optional auto-push** after commit
- 📁 **Smart commit-all**, grouping changes by context
- 🔗 **Branch-based PR creation**
- 🎯 **Strict Conventional Commits compliance**
- ⚙️ **Fully configurable prompts per project or globally**
- 🧪 **Type-safe, tested, production-ready**

---

## 🚀 Quick Start (2 minutes)

### Requirements

- Python **3.13+**
- Git
- Google Gemini API key
- GitHub CLI (`gh`) *(optional, for PR creation)*

### Install

```bash
uv tool install parcky-cli
```

### Configure

Get your API key at: https://makersuite.google.com/app/apikey

Then configure your environment (example):

```bash
parcky-cli setup
```

### Common usage

```bash
# AI-powered commit (with push)
parcky-cli smart-commit

# Commit without pushing
parcky-cli smart-commit --no-push

# Commit and create a PR
parcky-cli smart-commit --pr

# Commit all changes grouped by context
parcky-cli smart-commit-all

# Create PR from current branch
parcky-cli create-pr

# Create PR against another base
parcky-cli create-pr --base develop
```

---

## 🧠 How Pull Requests are generated

AI CLI analyzes:

- all commits in the branch
- all changed files (including additions/removals)
- diff stats and curated patches
- configuration and public interface changes

It then generates a PR with a stable structure:

- What was done
- Why it was done
- How to test
- Risk & impact (when applicable)

This avoids shallow or misleading PR descriptions.

---

## 🎨 Customizing AI Prompts

All AI behavior is customizable via `prompts.json`.
Lookup order:

1. `./prompts.json` (project-level)
2. `~/.config/ai-cli/prompts.json` (global)
3. Built-in defaults

Example:

```json
{
  "commit_message": {
    "description": "Commit message prompt",
    "prompt": "Generate a Conventional Commit message..."
  },
  "pull_request": {
    "description": "PR prompt",
    "prompt": "Generate a PR title and body..."
  }
}
```

You can:

- Change language
- Enforce stricter formats
- Customize PR structure
- Adapt prompts per repository

---

## ⚙️ Configuration

Environment variables:

- `GEMINI_API_KEY` — Gemini API key (required)
- `GEMINI_MODEL` — Model to use (default: `gemini-2.5-flash`)
- `MAX_DIFF_SIZE` — Max diff size sent to AI (default: `10000`)
- `DEFAULT_BRANCH` — Default git base branch (default: `main`)
- `DEBUG` — Debug mode (default: `false`)

---

## 🏗️ Architecture (for contributors)

AI CLI follows a clean, layered architecture:

```
src/ai_cli/
├── core/            # Domain models, interfaces, exceptions
├── services/        # Business logic
├── infrastructure/  # Git, AI, GitHub integrations
├── cli/             # Command-line interface
└── config/          # Configuration management
```

The design emphasizes:

- separation of concerns
- testability
- deterministic AI inputs
- safe fallbacks when AI is unavailable

---

## 🔧 Development

```bash
# Install dev dependencies
uv sync --group dev

# Format & lint
uv run ruff format src tests
uv run ruff check src tests

# Type checking
mypy src

# Run tests
pytest
```

---

## 🔄 Workflow

1. Analyze git changes
2. Generate commit or PR with AI
3. Show preview
4. User approves
5. Commit / Push / PR

AI is always assistive, never destructive.

---

## 🤝 Contributing

Contributions are welcome!

- Fork the repo
- Create a feature branch
- Make changes
- Run tests
- Commit with Conventional Commits
- Open a PR

---

## 📄 License

MIT License — see LICENSE.

Made with ❤️ by [Parcky](https://github.com/Parckyzin).
