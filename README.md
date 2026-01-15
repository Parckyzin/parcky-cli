# AI CLI 🤖

AI-powered git commit and pull request creation tool using Google Gemini.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

## ✨ Features

- 🤖 **AI-Powered Commits**: Generate conventional commit messages using Google Gemini (latest google.genai package)
- 📋 **Smart Pull Requests**: Create PR titles and descriptions automatically
- 🚀 **Auto Push**: Automatically push commits to remote repository
- 📁 **Smart Commit All**: Commit all changes grouped by folder and context
- 🔗 **Branch-based PRs**: Create PRs based on all changes in a branch
- 🎯 **Conventional Commits**: Follows the conventional commits specification
- 🛡️ **Type Safety**: Fully typed with mypy support
- 🧪 **Well Tested**: Comprehensive test suite with pytest
- 📦 **Professional Structure**: Clean architecture with proper separation of concerns
- ⚙️ **Pydantic Settings**: Modern configuration management with validation
- 📋 **Taskipy Integration**: Convenient task runner for development workflow

## 🏗️ Architecture

The project follows a clean architecture pattern with well-defined layers:

```
src/ai_cli/
├── core/           # Domain models, interfaces, and exceptions
├── services/       # Business logic and orchestration
├── infrastructure/ # External integrations (Git, AI, GitHub)
├── cli/           # Command-line interface
└── config/        # Configuration management
```

### Layers Overview

- **Core Layer**: Domain models, business interfaces, and custom exceptions
- **Services Layer**: Business logic and workflow orchestration
- **Infrastructure Layer**: External service integrations (Git, AI APIs, GitHub CLI)
- **CLI Layer**: User interface and command handling
- **Config Layer**: Environment-based configuration management

## 🚀 Installation

### Requirements

- Python 3.13 or higher (recommended)
- Git
- [GitHub CLI](https://cli.github.com/) (optional, for PR creation)
- Google Gemini API key

### Quick Setup

1. **Install using uv (recommended):**
   ```bash
   # Clone and install
   git clone <repository-url>
   cd ai-cli
   uv sync
   
   # Install globally
   uv tool install .
   ```

2. **Configure your API key:**
   ```bash
   # Interactive setup (easiest)
   ai-cli setup
   
   # Or set directly
   ai-cli setup --api-key YOUR_API_KEY
   ```

   Get your API key from: https://makersuite.google.com/app/apikey

3. **Start using:**
   ```bash
   ai-cli smart-commit    # AI-powered commits
   ai-cli create-pr       # Create PRs
   ai-cli --help          # See all commands
   ```

### Alternative Setup Methods

<details>
<summary>Manual .env configuration</summary>

```bash
# Generate .env file with all options
python scripts/env-gen.py --stdout  # Preview
python scripts/env-gen.py           # Generate local .env
python scripts/env-gen.py --global  # Generate global config
```

</details>

<details>
<summary>Install GitHub CLI (optional, for PR creation)</summary>

```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install GitHub.cli
```

</details>

6. **Install globally (to use in other projects):**
   ```bash
   uv tool install .
   ```

   Configuration is stored at `~/.config/ai-cli/.env`

## 📖 Usage

### Basic Usage

Stage your changes and run the smart commit:

```bash
git add .
ai-cli smart-commit
```

### Available Commands

```bash
# Basic commit (with push)
ai-cli smart-commit

# Commit without pushing
ai-cli smart-commit --no-push

# Commit with automatic PR creation
ai-cli smart-commit --pr

# Auto-confirm all prompts
ai-cli smart-commit --yes

# Commit ALL changes with smart grouping by folder
ai-cli smart-commit-all

# Create PR based on current branch changes
ai-cli create-pr

# Create PR against specific base branch
ai-cli create-pr --base develop

# Create a new GitHub repository
ai-cli create-repo my-project --visibility public --description "My project"

# Show version
ai-cli version
```

### Command Reference

| Command | Description |
|---------|-------------|
| `setup` | Configure ai-cli with your API key (interactive or direct) |
| `config` | Show configuration status and file locations |
| `smart-commit` | Create AI-powered commit from staged changes |
| `smart-commit-all` | Commit all changes with smart grouping by folder |
| `create-pr` | Create PR based on current branch changes |
| `create-repo` | Create a new GitHub repository |
| `version` | Show version information |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required) | - |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `GEMINI_SYSTEM_INSTRUCTION` | AI system instruction | Default DevOps instruction |
| `MAX_DIFF_SIZE` | Maximum diff size for AI analysis | `10000` |
| `DEFAULT_BRANCH` | Default git branch | `main` |
| `DEBUG` | Enable debug mode | `false` |

### 🎨 Customizing AI Prompts

You can customize all AI prompts by editing the `prompts.json` file. The tool looks for prompts in this order:

1. `./prompts.json` (project directory - highest priority)
2. `~/.config/ai-cli/prompts.json` (global config)
3. Built-in defaults (fallback)

**Available prompts:**

| Key | Description |
|-----|-------------|
| `commit_message` | Prompt for generating commit messages |
| `pull_request` | Prompt for generating PR title and description |
| `file_correlation` | Prompt for analyzing which files should be committed together |
| `system_instruction` | System instruction for the AI model |

**Example `prompts.json`:**

```json
{
  "commit_message": {
    "description": "Prompt for generating commit messages",
    "prompt": "Generate a commit message following Conventional Commits..."
  },
  "pull_request": {
    "description": "Prompt for generating PR content",
    "prompt": "Create a title and description for a Pull Request..."
  }
}
```

This allows you to:
- Change the language of generated messages
- Modify the commit message format
- Customize PR templates
- Adjust AI behavior per project

## 🔧 Development

### Setup Development Environment

```bash
# Install development dependencies
uv sync --group dev

# Install pre-commit hooks
pre-commit install
```

### Code Quality

```bash
# Format code
uv run ruff format src tests

# Lint code
uv run ruff check src tests

# Fix lint issues automatically
uv run ruff check src tests --fix

# Type checking
mypy src

# Run all checks
uv run task check
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ai_cli

# Run only unit tests
pytest tests/unit

# Run only integration tests
pytest tests/integration
```

### Project Structure

```
ai-cli/
├── src/ai_cli/              # Main application code
│   ├── core/                # Domain layer
│   │   ├── models.py        # Domain models
│   │   ├── interfaces.py    # Abstract interfaces
│   │   └── exceptions.py    # Custom exceptions
│   ├── services/            # Business logic layer
│   │   └── smart_commit_service.py
│   ├── infrastructure/      # Infrastructure layer
│   │   ├── git_repository.py    # Git operations
│   │   ├── ai_service.py        # AI integration
│   │   └── pr_service.py        # GitHub PR service
│   ├── cli/                 # Presentation layer
│   │   └── main.py          # CLI interface
│   └── config/              # Configuration layer
│       └── settings.py      # App configuration
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── conftest.py         # Test fixtures
├── pyproject.toml          # Project configuration
├── README.md               # This file
└── .env.example            # Environment template
```

## 🔄 Workflow

The AI CLI follows this workflow:

1. **Analyze**: Examines staged git changes
2. **Generate**: Creates commit message using AI
3. **Review**: Presents suggestion for user approval
4. **Commit**: Creates git commit with the message
5. **Push**: Pushes changes to remote (optional)
6. **PR**: Creates pull request with AI-generated description (optional)

## 🎯 Conventional Commits

The tool generates commits following the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Supported Types

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `chore`: Maintenance tasks
- `build`: Build system changes
- `ci`: CI/CD changes
- `perf`: Performance improvements
- `revert`: Reverts previous commits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and quality checks
5. Commit using conventional commits
6. Push to your branch
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) for AI capabilities (using latest google.genai package)
- [Typer](https://typer.tiangolo.com/) for CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [Ruff](https://github.com/astral-sh/ruff) for fast linting and formatting
- [Conventional Commits](https://www.conventionalcommits.org/) for commit standards
- [Pydantic](https://pydantic.dev/) for settings management and validation
- [Taskipy](https://github.com/taskipy/taskipy) for task automation

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-repo/ai-cli/issues) page
2. Create a new issue with detailed information
3. Include error messages and environment details

---

Made with ❤️ by developers, for developers.
