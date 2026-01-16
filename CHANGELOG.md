# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: Migrated from deprecated `google-generativeai` to `google-genai` package
- Updated AI service implementation to use new `google.genai.Client` API
- Updated default model to `gemini-1.5-flash` for better compatibility
- Enhanced configuration management with Pydantic Settings v2
- Added comprehensive taskipy tasks for development workflow

### Added
- Pydantic-based configuration management with validation
- Field validators for configuration parameters
- Enhanced task automation with taskipy
- New development tasks: security checks, dependency auditing, environment validation
- Better error handling for configuration issues
- Support for nested configuration sections (AI, Git, App)

### Fixed
- Pydantic v2 compatibility with `@field_validator` decorators
- Configuration loading with proper error handling
- Environment variable validation and defaults

### Added
- Complete project restructuring with clean architecture
- Domain-driven design with separated layers:
  - Core layer (models, interfaces, exceptions)
  - Services layer (business logic)
  - Infrastructure layer (external integrations)
  - CLI layer (user interface)
  - Configuration layer (settings management)
- Comprehensive test suite with pytest
- Type safety with mypy support
- Code quality tools (black, isort, flake8)
- Pre-commit hooks for code quality
- Professional development workflow with Makefile
- Detailed documentation and README
- MIT License
- Environment-based configuration management
- Clean separation of concerns
- Dependency injection pattern
- Error handling with custom exceptions
- Rich CLI interface with beautiful output
- Coverage reporting

### Changed
- Refactored monolithic main.py into proper modules
- Improved error handling and user feedback
- Enhanced code organization and maintainability
- Better separation between business logic and infrastructure

### Technical Improvements
- Added abstract interfaces for testability
- Implemented proper dependency injection
- Created comprehensive test fixtures
- Added configuration management layer
- Improved type annotations throughout codebase
- Added proper package structure with __init__.py files

### Development Experience
- Added Makefile for common development tasks
- Set up pre-commit hooks for code quality
- Added pytest configuration with coverage
- Created development dependencies group
- Added example environment configuration

## [2026.01.a02] - Initial Version

### Added
- Basic AI-powered commit message generation
- Simple CLI interface with typer
- Google Gemini integration
- Basic git operations
