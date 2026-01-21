"""
Prompts loader for AI CLI application.
Loads prompts from JSON file for easy customization.
"""

import json
from pathlib import Path
from typing import Any

from . import paths

class PromptsLoader:
    """Load and manage prompts from JSON file."""

    _instance: "PromptsLoader | None" = None
    _prompts: dict[str, Any] = {}

    def __new__(cls) -> "PromptsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_prompts()
        return cls._instance

    def _get_prompts_paths(self) -> list[Path]:
        """Get list of possible prompts.json locations in priority order."""
        search_paths: list[Path] = []

        local_prompts = paths.get_local_prompts_path()
        if local_prompts.exists():
            search_paths.append(local_prompts)

        global_prompts = paths.get_global_prompts_path()
        if global_prompts.exists():
            search_paths.append(global_prompts)

        package_prompts = paths.get_package_prompts_path()
        if package_prompts.exists():
            search_paths.append(package_prompts)

        return search_paths

    def _load_prompts(self) -> None:
        """Load prompts from JSON file."""
        paths = self._get_prompts_paths()

        if not paths:
            # Use hardcoded defaults if no file found
            self._prompts = self._get_default_prompts()
            return

        # Load from first available file (highest priority)
        try:
            with open(paths[0], encoding="utf-8") as f:
                self._prompts = json.load(f)
        except (json.JSONDecodeError, OSError):
            self._prompts = self._get_default_prompts()

    def _get_default_prompts(self) -> dict[str, Any]:
        """Return default prompts if no file is found."""
        return {
            "commit_message": {
                "prompt": (
                    "Generate a commit message following the 'Conventional Commits' pattern.\n"
                    "Format: <type>(<scope>): <subject>\n\n"
                    "Valid types: feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert\n\n"
                    "Rules:\n"
                    "1. Use English for the message\n"
                    "2. Keep the subject concise (maximum 50 characters)\n"
                    '3. Use imperative mood ("add" not "added")\n'
                    "4. Don't use period at the end of the subject\n\n"
                    "Return only the message, without quotes or extra explanations."
                )
            },
            "pull_request": {
                "prompt": (
                    "Create a title and description for a Pull Request based on the changes.\n"
                    "The format must be Markdown.\n\n"
                    "Required structure:\n"
                    "Title: [Short and clear title suggestion]\n"
                    "Body:\n"
                    "## What was done\n"
                    "- List the main changes clearly\n\n"
                    "## Why it was done\n"
                    "- Explain the motivation\n\n"
                    "## How to test\n"
                    "- Provide steps to validate"
                )
            },
            "file_correlation": {
                "prompt": (
                    "Analyze these changed files and determine which should be committed together.\n"
                    "Respond with groups in this format:\n"
                    "GROUP: file1.py, file2.py\n"
                    "GROUP: file3.py"
                )
            },
            "system_instruction": {
                "prompt": (
                    "You are a senior DevOps engineer obsessed with best practices "
                    "and Conventional Commits."
                )
            },
        }

    def get_prompt(self, key: str) -> str:
        """Get a prompt by key."""
        if key in self._prompts:
            return self._prompts[key].get("prompt", "")
        return ""

    def get_all_prompts(self) -> dict[str, Any]:
        """Get all prompts."""
        return self._prompts.copy()

    def reload(self) -> None:
        """Reload prompts from file."""
        self._load_prompts()


# Global instance for easy access
_loader: PromptsLoader | None = None


def get_prompt(key: str) -> str:
    """Get a prompt by key."""
    global _loader
    if _loader is None:
        _loader = PromptsLoader()
    return _loader.get_prompt(key)


def reload_prompts() -> None:
    """Reload prompts from file."""
    global _loader
    if _loader is None:
        _loader = PromptsLoader()
    _loader.reload()
