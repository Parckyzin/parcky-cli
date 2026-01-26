"""
Unit tests for smart commit service.
"""

from unittest.mock import Mock, patch

import pytest

from ai_cli.core.exceptions import AIServiceError, NoStagedChangesError
from ai_cli.core.models import GitDiff
from ai_cli.services.smart_commit_service import SmartCommitService


class TestSmartCommitService:
    """Test SmartCommitService."""

    def test_get_staged_changes(self, smart_commit_service, sample_git_diff):
        """Test getting staged changes."""
        smart_commit_service.git_repo.get_staged_diff.return_value = sample_git_diff

        result = smart_commit_service.get_staged_changes()

        assert result == sample_git_diff
        smart_commit_service.git_repo.get_staged_diff.assert_called_once()

    def test_generate_commit_message(self, smart_commit_service, sample_git_diff):
        """Test generating commit message."""
        expected_message = "feat: add new feature"
        smart_commit_service.git_repo.get_staged_file_paths.return_value = [
            "src/app.py"
        ]
        smart_commit_service.ai_service.generate_commit_message.return_value = (
            expected_message
        )

        with patch(
            "ai_cli.pipelines.commit_message.build_commit_context",
            return_value="context",
        ) as build_context:
            result = smart_commit_service.generate_commit_message(sample_git_diff)

        assert result == expected_message
        build_context.assert_called_once_with(sample_git_diff, ["src/app.py"])
        expected_diff = GitDiff(
            content="context", is_truncated=sample_git_diff.is_truncated
        )
        smart_commit_service.ai_service.generate_commit_message.assert_called_once_with(
            expected_diff
        )

    def test_generate_commit_message_fallback(
        self, smart_commit_service, sample_git_diff
    ):
        """Test fallback when AI fails."""
        smart_commit_service.git_repo.get_staged_file_paths.return_value = [
            "src/app.py",
            "src/utils.py",
        ]
        smart_commit_service.ai_service.generate_commit_message.side_effect = (
            AIServiceError("boom")
        )

        with patch(
            "ai_cli.pipelines.commit_message.build_commit_context",
            return_value="context",
        ):
            result = smart_commit_service.generate_commit_message(sample_git_diff)

        assert result == "chore: update 2 files"

    def test_create_commit(self, smart_commit_service):
        """Test creating commit."""
        message = "feat: add new feature"
        smart_commit_service.git_repo.commit.return_value = True

        result = smart_commit_service.create_commit(message)

        assert result is True
        smart_commit_service.git_repo.commit.assert_called_once_with(message)

    def test_push_changes_with_auto_push_true(
        self, smart_commit_service, sample_git_branch
    ):
        """Test pushing changes with auto push enabled."""
        smart_commit_service.git_repo.get_current_branch.return_value = (
            sample_git_branch
        )
        smart_commit_service.git_repo.push.return_value = True

        result = smart_commit_service.push_changes(auto_push=True)

        assert result is True
        smart_commit_service.git_repo.get_current_branch.assert_called_once()
        smart_commit_service.git_repo.push.assert_called_once_with(
            sample_git_branch.name
        )

    def test_push_changes_with_auto_push_false(self, smart_commit_service):
        """Test pushing changes with auto push disabled."""
        result = smart_commit_service.push_changes(auto_push=False)

        assert result is True
        smart_commit_service.git_repo.get_current_branch.assert_not_called()
        smart_commit_service.git_repo.push.assert_not_called()

    def test_create_pull_request(
        self, smart_commit_service, sample_git_diff, sample_pull_request
    ):
        """Test creating pull request."""
        commit_msg = "feat: add new feature"
        smart_commit_service.ai_service.generate_pull_request.return_value = (
            sample_pull_request
        )
        smart_commit_service.pr_service.create_pull_request.return_value = True

        result = smart_commit_service.create_pull_request(sample_git_diff, commit_msg)

        assert result is True
        smart_commit_service.ai_service.generate_pull_request.assert_called_once_with(
            sample_git_diff, commit_msg
        )
        smart_commit_service.pr_service.create_pull_request.assert_called_once_with(
            sample_pull_request
        )

    def test_create_pull_request_without_service(
        self, mock_git_repository, mock_ai_service
    ):
        """Test creating pull request without PR service configured."""
        service = SmartCommitService(
            git_repo=mock_git_repository, ai_service=mock_ai_service, pr_service=None
        )

        with pytest.raises(ValueError, match="PR service not configured"):
            service.create_pull_request(Mock(), "test message")

    def test_execute_smart_commit_success(
        self,
        smart_commit_service,
        sample_git_diff,
        sample_git_branch,
        sample_pull_request,
    ):
        """Test successful smart commit execution."""
        # Setup mocks
        smart_commit_service.git_repo.get_staged_diff.return_value = sample_git_diff
        smart_commit_service.git_repo.get_staged_file_paths.return_value = [
            "src/app.py"
        ]
        smart_commit_service.ai_service.generate_commit_message.return_value = (
            "feat: add feature"
        )
        smart_commit_service.git_repo.commit.return_value = True
        smart_commit_service.git_repo.get_current_branch.return_value = (
            sample_git_branch
        )
        smart_commit_service.git_repo.push.return_value = True
        smart_commit_service.ai_service.generate_pull_request.return_value = (
            sample_pull_request
        )
        smart_commit_service.pr_service.create_pull_request.return_value = True

        with patch(
            "ai_cli.pipelines.commit_message.build_commit_context",
            return_value="context",
        ):
            result = smart_commit_service.execute_smart_commit(
                auto_push=True, create_pr=True
            )

        assert result["diff_retrieved"] is True
        assert result["commit_created"] is True
        assert result["pushed"] is True
        assert result["pr_created"] is True
        assert result["diff"] == sample_git_diff
        assert result["commit_message"] == "feat: add feature"
        assert result["branch"] == sample_git_branch.name
        assert len(result["errors"]) == 0

    def test_execute_smart_commit_with_error(self, smart_commit_service):
        """Test smart commit execution with error."""
        # Setup mock to raise exception
        smart_commit_service.git_repo.get_staged_diff.side_effect = (
            NoStagedChangesError("No changes")
        )

        result = smart_commit_service.execute_smart_commit()

        assert result["diff_retrieved"] is False
        assert result["commit_created"] is False
        assert result["pushed"] is False
        assert result["pr_created"] is False
        assert len(result["errors"]) == 1
        assert "No changes" in result["errors"][0]
