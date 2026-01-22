"""
Cache system for AI CLI to store user preferences like model history.
"""

import hashlib
import json
from typing import Any

from ai_cli.config import paths


class Cache:
    """Simple JSON-based cache for storing user preferences."""

    def __init__(self):
        self.cache_file = paths.get_cache_path()
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
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self._data, indent=2))

    def _get_defaults(self) -> dict[str, Any]:
        """Get default cache values."""
        return {
            "ai_responses": {},
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in cache."""
        self._data[key] = value
        self._save()

    @staticmethod
    def make_ai_cache_key(
        model_name: str,
        prompt: str,
        context: str,
        temperature: float,
        max_tokens: int | None,
    ) -> str:
        """Create a stable cache key without storing raw content."""
        payload = f"{model_name}|{temperature}|{max_tokens}|{prompt}|{context}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def is_safe_for_cache(self, *texts: str) -> bool:
        """Check whether content is safe to cache (no obvious secrets)."""
        secret_markers = (
            "API_KEY",
            "SECRET",
            "TOKEN",
            "PASSWORD",
            "PRIVATE_KEY",
            "BEGIN RSA PRIVATE KEY",
            "BEGIN PRIVATE KEY",
        )
        for text in texts:
            upper_text = text.upper()
            if any(marker in upper_text for marker in secret_markers):
                return False
        return True

    def get_ai_response(self, key: str) -> str | None:
        """Get a cached AI response if present."""
        responses = self._data.get("ai_responses", {})
        entry = responses.get(key)
        if not entry:
            return None
        return entry.get("response")

    def set_ai_response(self, key: str, response: str, max_entries: int = 200) -> None:
        """Store an AI response with basic pruning."""
        responses = self._data.setdefault("ai_responses", {})
        responses[key] = {"response": response}
        if len(responses) > max_entries:
            for old_key in list(responses.keys())[: len(responses) - max_entries]:
                responses.pop(old_key, None)
        self._save()


_cache: Cache | None = None


def get_cache() -> Cache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache
