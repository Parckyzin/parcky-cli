"""
Test configuration and fixtures.
"""

from unittest.mock import Mock

import pytest

from ai_cli.clients.gemini import GeminiAIService
from ai_cli.config.settings import AIConfig, AppConfig, GitConfig
from ai_cli.core.models import GitBranch, GitDiff, PullRequest
from ai_cli.infrastructure.git_repository import GitRepository
from ai_cli.services.smart_commit_service import SmartCommitService


@pytest.fixture
def mock_git_config():
    """Mock git configuration."""
    return GitConfig(max_diff_size=1000, default_branch="main")


@pytest.fixture
def mock_ai_config():
    """Mock AI configuration."""
    return AIConfig(
        api_key="test-api-key",
        model_name="test-model",
        system_instruction="test instruction",
    )


@pytest.fixture
def mock_app_config(mock_ai_config, mock_git_config):
    """Mock application configuration."""
    return AppConfig(ai=mock_ai_config, git=mock_git_config, debug=True)


@pytest.fixture
def sample_git_diff():
    """Sample git diff for testing."""
    return GitDiff(
        content="""diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def hello():
+    print("world")
     return "hello"
""",
        is_truncated=False,
    )


@pytest.fixture
def sample_git_branch():
    """Sample git branch for testing."""
    return GitBranch(name="feature/test-branch")


@pytest.fixture
def sample_pull_request():
    """Sample pull request for testing."""
    return PullRequest(
        title="feat: add new feature",
        body="""## O que foi feito
- Added new feature
- Updated documentation

## Por que foi feito
- To improve user experience

## Como testar
- Run the tests
""",
    )


@pytest.fixture
def mock_git_repository(mock_git_config):
    """Mock git repository."""
    mock_repo = Mock(spec=GitRepository)
    mock_repo.config = mock_git_config
    return mock_repo


@pytest.fixture
def mock_ai_service():
    """Mock AI service."""
    mock_service = Mock(spec=GeminiAIService)
    return mock_service


@pytest.fixture
def mock_pr_service():
    """Mock PR service."""
    mock_service = Mock()
    return mock_service


@pytest.fixture
def smart_commit_service(mock_git_repository, mock_ai_service, mock_pr_service):
    """Smart commit service with mocked dependencies."""
    return SmartCommitService(
        git_repo=mock_git_repository,
        ai_service=mock_ai_service,
        pr_service=mock_pr_service,
    )
