#!/bin/bash

# Advanced development tasks for AI CLI
# Usage: ./tasks.sh <task_name>

set -e

TASK=${1:-help}

case $TASK in
    "help")
        echo "Available tasks:"
        echo "  setup-dev      - Setup complete development environment"
        echo "  test-all       - Run all tests with coverage"
        echo "  test-watch     - Run tests in watch mode"
        echo "  lint-fix       - Run linting and auto-fix issues"
        echo "  type-check     - Run mypy type checking"
        echo "  security-check - Run security checks"
        echo "  deps-check     - Check for dependency vulnerabilities"
        echo "  profile        - Profile the application"
        echo "  benchmark      - Run performance benchmarks"
        echo "  release        - Prepare for release"
        echo "  clean-all      - Clean all generated files"
        echo "  validate-env   - Validate environment configuration"
        ;;
    
    "setup-dev")
        echo "🚀 Setting up development environment..."
        uv sync --group dev
        pre-commit install
        echo "✅ Development environment ready!"
        ;;
    
    "test-all")
        echo "🧪 Running all tests with coverage..."
        PYTHONPATH=. uv run pytest --cov=src/ai_cli --cov-report=html --cov-report=term-missing
        echo "📊 Coverage report generated in htmlcov/"
        ;;
    
    "test-watch")
        echo "👀 Running tests in watch mode..."
        PYTHONPATH=. uv run pytest-watch --runner "pytest --tb=short"
        ;;
    
    "lint-fix")
        echo "🔧 Running linting and auto-fixing..."
        uv run black src tests
        uv run isort src tests
        uv run flake8 src tests
        echo "✅ Code formatted and linted!"
        ;;
    
    "type-check")
        echo "🔍 Running type checking..."
        uv run mypy src
        echo "✅ Type checking complete!"
        ;;
    
    "security-check")
        echo "🔐 Running security checks..."
        uv run bandit -r src/
        echo "✅ Security check complete!"
        ;;
    
    "deps-check")
        echo "📦 Checking dependencies for vulnerabilities..."
        uv run safety check
        echo "✅ Dependencies checked!"
        ;;
    
    "profile")
        echo "⏱️ Profiling application..."
        PYTHONPATH=. uv run python -m cProfile -o profile.stats main.py --help
        echo "📊 Profile saved to profile.stats"
        ;;
    
    "benchmark")
        echo "🏃 Running performance benchmarks..."
        # Add performance tests here
        echo "⚡ Benchmarks complete!"
        ;;
    
    "release")
        echo "🚀 Preparing for release..."
        ./tasks.sh clean-all
        ./tasks.sh test-all
        ./tasks.sh lint-fix
        ./tasks.sh type-check
        uv build
        echo "✅ Release ready!"
        ;;
    
    "clean-all")
        echo "🧹 Cleaning all generated files..."
        rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage .pytest_cache/
        find . -type d -name __pycache__ -delete
        find . -type f -name "*.pyc" -delete
        find . -type f -name "*.pyo" -delete
        find . -type f -name "profile.stats" -delete
        echo "✅ Cleanup complete!"
        ;;
    
    "validate-env")
        echo "🔍 Validating environment configuration..."
        PYTHONPATH=. uv run python -c "
from src.ai_cli.config.settings import AppConfig
try:
    config = AppConfig.load()
    print('✅ Configuration is valid!')
    print(f'Debug mode: {config.debug}')
    print(f'AI Model: {config.ai.model_name}')
    print(f'Git branch: {config.git.default_branch}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"
        ;;
    
    *)
        echo "❌ Unknown task: $TASK"
        echo "Run './tasks.sh help' for available tasks"
        exit 1
        ;;
esac
