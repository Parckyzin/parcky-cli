"""
Cache system for AI CLI to store user preferences like model history.
"""

import json
from pathlib import Path
from typing import Any


class Cache:
    """Simple JSON-based cache for storing user preferences."""

    def __init__(self):
        self.cache_dir = Path.home() / ".config" / "ai-cli"
        self.cache_file = self.cache_dir / "cache.json"
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                self._data = json.loads(self.cache_file.read_text())
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = self._get_defaults()

    def _save(self) -> None:
        """Save cache to file."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self._data, indent=2))

    def _get_defaults(self) -> dict[str, Any]:
        """Get default cache values."""
        return {
            "model_history": [
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ]
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in cache."""
        self._data[key] = value
        self._save()

    # Model history specific methods
    def get_model_history(self) -> list[str]:
        """Get list of previously used models."""
        return self._data.get("model_history", self._get_defaults()["model_history"])

    def add_model_to_history(self, model: str) -> None:
        """Add a model to history (moves to top if exists)."""
        history = self.get_model_history()
        # Remove if already exists
        if model in history:
            history.remove(model)
        # Add to top
        history.insert(0, model)
        # Keep max 10 models
        self._data["model_history"] = history[:10]
        self._save()

    def remove_model_from_history(self, model: str) -> bool:
        """Remove a model from history. Returns True if removed."""
        history = self.get_model_history()
        if model in history:
            history.remove(model)
            self._data["model_history"] = history
            self._save()
            return True
        return False


# Global cache instance
_cache: Cache | None = None


def get_cache() -> Cache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache
