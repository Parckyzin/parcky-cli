"""
Unit tests for AI robustness and caching.
"""

import hashlib
from unittest.mock import Mock

from ai_cli.clients import gemini as gemini_module
from ai_cli.config.settings import AIConfig, GitConfig
from ai_cli.core.exceptions import AIServiceError
from ai_cli.core.models import GitDiff, PRDiffStats, PRFileChange
from ai_cli.infrastructure.git_repository import GitRepository
from ai_cli.services.create_pr_service import BranchInfo, CreatePRService


class FakeCache:
    """In-memory cache replacement for tests."""

    def __init__(self):
        self.responses = {}
        self.set_calls = 0

    def make_ai_cache_key(
        self,
        model_name: str,
        prompt: str,
        context: str,
        temperature: float,
        max_tokens: int | None,
    ) -> str:
        payload = f"{model_name}|{temperature}|{max_tokens}|{prompt}|{context}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def is_safe_for_cache(self, *_texts: str) -> bool:
        return True

    def get_ai_response(self, key: str) -> str | None:
        return self.responses.get(key)

    def set_ai_response(self, key: str, response: str, _max_entries: int = 200) -> None:
        self.responses[key] = response
        self.set_calls += 1


class FakeResponse:
    """Fake response wrapper."""

    def __init__(self, text: str):
        self.text = text


class FakeModels:
    """Fake models client for tests."""

    def __init__(self):
        self.calls = 0

    def generate_content(self, model: str, contents: str, config):
        self.calls += 1
        self.last_args = (model, contents, config)
        return FakeResponse("feat: cached response")


class FakeClient:
    """Fake Gemini client for tests."""

    def __init__(self, api_key: str):
        self._api_key = api_key
        self.models = FakeModels()


def test_build_ai_context_limits_diff():
    config = GitConfig(max_diff_size=1000, default_branch="main")
    repo = GitRepository(config)
    diff_content = "diff --git a/a.txt b/a.txt\n" + "\n".join(
        f"+line{i}" for i in range(200)
    )
    diff = GitDiff(content=diff_content, is_truncated=True)

    context = repo.build_commit_context(diff, max_example_lines=10)

    assert "SUMMARY" in context
    assert "EXAMPLES" in context
    assert "+line0" in context
    assert "+line50" not in context


def test_gemini_cache_hit_and_miss(monkeypatch):
    fake_cache = FakeCache()
    monkeypatch.setattr(gemini_module, "get_cache", lambda: fake_cache)
    monkeypatch.setattr(gemini_module.genai, "Client", FakeClient)

    config = AIConfig(
        api_key="test",
        model_name="test-model",
        system_instruction="test",
        cache_enabled=True,
    )
    service = gemini_module.GeminiAIService(config)
    diff = GitDiff(content="diff", is_truncated=False)

    first = service.generate_commit_message(diff)
    second = service.generate_commit_message(diff)

    assert first == "feat: cached response"
    assert second == "feat: cached response"
    assert service.client.models.calls == 1
    assert fake_cache.set_calls == 1


def test_create_pr_fallback_on_ai_failure():
    git_repo = Mock()
    ai_service = Mock()
    pr_service = Mock()

    git_repo.build_ai_context.return_value = "context"
    git_repo.get_branch_patch.return_value = "diff --git a/a b/a\n@@\n+change"
    ai_service.generate_pull_request.side_effect = AIServiceError("boom")

    service = CreatePRService(
        git_repo=git_repo,
        ai_service=ai_service,
        pr_service=pr_service,
        max_context_chars=35000,
    )
    branch_info = BranchInfo(
        name="feature/test",
        base_branch="main",
        commits=["feat: add x"],
        files_changed=["src/app.py"],
        name_status=[PRFileChange(path="src/app.py", status="M")],
        diff_stats=PRDiffStats(
            files=[],
            total_files=1,
            total_insertions=1,
            total_deletions=0,
        ),
    )

    pr = service.generate_pr_content(branch_info)

    assert pr.title == "chore: update feature/test"
    assert "fallback" in pr.body.lower()
