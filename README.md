# AI CLI 🤖

AI-powered git commit and pull request creation tool using Google Gemini.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

## ✨ Features

- 🤖 **AI-Powered Commits**: Generate conventional commit messages using Google Gemini (latest google.genai package)
- 📋 **Smart Pull Requests**: Create PR titles and descriptions automatically
- 🚀 **Auto Push**: Automatically push commits to remote repository
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

- Python 3.9 or higher
- Git
- [GitHub CLI](https://cli.github.com/) (optional, for PR creation)
- Google Gemini API key

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ai-cli
   ```

2. **Install dependencies using uv (recommended):**
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -e .
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Get Google Gemini API Key:**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add it to your `.env` file

5. **Install GitHub CLI (optional, for PR creation):**
   ```bash
   # macOS
   brew install gh

   # Ubuntu/Debian
   sudo apt install gh

   # Windows
   winget install GitHub.cli
   ```

## 📖 Usage

### Basic Usage

Stage your changes and run the smart commit:

```bash
git add .
ai-cli smart-commit
```

### Command Options

```bash
# Basic commit (with push)
ai-cli smart-commit

# Commit without pushing
ai-cli smart-commit --no-push

# Commit with automatic PR creation
ai-cli smart-commit --pr

# Auto-confirm all prompts
ai-cli smart-commit --yes

# Combine options
ai-cli smart-commit --pr --yes
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required) | - |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `GEMINI_SYSTEM_INSTRUCTION` | AI system instruction | Default DevOps instruction |
| `MAX_DIFF_SIZE` | Maximum diff size for AI analysis | `10000` |
| `DEFAULT_BRANCH` | Default git branch | `main` |
| `DEBUG` | Enable debug mode | `false` |

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
black src tests

# Sort imports
isort src tests

# Lint code
flake8 src tests

# Type checking
mypy src

# Run all checks
pre-commit run --all-files
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
