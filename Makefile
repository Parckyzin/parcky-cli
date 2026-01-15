# Makefile for AI CLI development

.PHONY: help install install-dev test test-cov lint format type-check clean build run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  test         Run all tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  test-unit    Run only unit tests"
	@echo "  test-integration  Run only integration tests"
	@echo "  lint         Run linting (flake8)"
	@echo "  format       Format code (black + isort)"
	@echo "  type-check   Run type checking (mypy)"
	@echo "  check        Run all quality checks"
	@echo "  clean        Clean up build artifacts"
	@echo "  build        Build the package"
	@echo "  run          Run the CLI application"
	@echo "  setup-dev    Setup complete development environment"
	@echo "  commit       Create AI-powered commit"
	@echo "  validate-env Validate environment configuration"
	@echo ""
	@echo "Taskipy commands (use 'uv run task <command>'):"
	@echo "  task test    Run tests"
	@echo "  task format  Format code"
	@echo "  task lint    Run linting"
	@echo "  task check   Run all checks"
	@echo "  task commit  Create smart commit"

# Installation
install:
	uv sync

install-dev:
	uv sync --group dev
	pre-commit install

# Testing (using taskipy)
test:
	uv run task test

test-cov:
	uv run task test-cov

test-unit:
	uv run task test-unit

test-integration:
	uv run task test-integration

# Code quality (using taskipy)
lint:
	uv run task lint

format:
	uv run task format

type-check:
	uv run task type-check

check:
	uv run task check

# Development workflow
setup-dev:
	uv run task setup-dev

# Cleanup
clean:
	uv run task clean

# Build
build:
	uv run task build

# Run application
run:
	uv run task run

cli:
	uv run task cli

version:
	uv run task version

# Git operations
commit:
	uv run task commit

commit-no-push:
	uv run task commit-no-push

commit-pr:
	uv run task commit-pr

commit-all:
	uv run task commit-all

commit-all-auto:
	uv run task commit-all-auto

# Pull Request operations
pr:
	uv run task pr

pr-auto:
	uv run task pr-auto

# Repository operations
create-repo:
	@echo "Usage: make create-repo NAME=<repo-name> [VISIBILITY=private] [DESC='description']"
	@test -n "$(NAME)" || (echo "Error: NAME is required" && exit 1)
	uv run ai-cli create-repo $(NAME) --visibility $(or $(VISIBILITY),private) $(if $(DESC),--description "$(DESC)",)

# Validation
validate-env:
	./tasks.sh validate-env

# Pre-commit hooks
pre-commit:
	pre-commit run --all-files

# Documentation
docs-serve:
	uv run task docs-serve
