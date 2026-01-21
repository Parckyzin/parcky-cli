"""
Unit tests for core models.
"""

import pytest

from ai_cli.core.models import (
    CommitMessage,
    CommitType,
    GitBranch,
    GitDiff,
    PullRequest,
)


class TestCommitMessage:
    """Test CommitMessage model."""

    def test_commit_message_creation(self):
        """Test commit message creation."""
        commit = CommitMessage(
            type=CommitType.FEAT, scope="auth", subject="add login validation"
        )

        assert commit.type == CommitType.FEAT
        assert commit.scope == "auth"
        assert commit.subject == "add login validation"

    def test_commit_message_str_with_scope(self):
        """Test commit message string representation with scope."""
        commit = CommitMessage(
            type=CommitType.FEAT, scope="auth", subject="add login validation"
        )

        assert str(commit) == "feat(auth): add login validation"

    def test_commit_message_str_without_scope(self):
        """Test commit message string representation without scope."""
        commit = CommitMessage(
            type=CommitType.FIX, scope=None, subject="resolve timeout issue"
        )

        assert str(commit) == "fix: resolve timeout issue"

    def test_full_message_with_body_and_footer(self):
        """Test full message with body and footer."""
        commit = CommitMessage(
            type=CommitType.FEAT,
            scope="api",
            subject="add user endpoint",
            body="Added new endpoint for user management",
            footer="Closes #123",
        )

        expected = """feat(api): add user endpoint

Added new endpoint for user management

Closes #123"""

        assert commit.full_message == expected


class TestGitDiff:
    """Test GitDiff model."""

    def test_git_diff_creation(self):
        """Test git diff creation."""
        diff = GitDiff(content="diff content", is_truncated=True)

        assert diff.content == "diff content"
        assert diff.is_truncated is True

    def test_is_empty_with_content(self):
        """Test is_empty with content."""
        diff = GitDiff(content="some diff content")

        assert not diff.is_empty

    def test_is_empty_with_whitespace(self):
        """Test is_empty with whitespace only."""
        diff = GitDiff(content="   \n  \t  ")

        assert diff.is_empty

    def test_is_empty_with_empty_string(self):
        """Test is_empty with empty string."""
        diff = GitDiff(content="")

        assert diff.is_empty


class TestPullRequest:
    """Test PullRequest model."""

    def test_pull_request_creation(self):
        """Test pull request creation."""
        pr = PullRequest(title="Add new feature", body="Description of the feature")

        assert pr.title == "Add new feature"
        assert pr.body == "Description of the feature"

    def test_formatted_body_escaping(self):
        """Test body formatting with quote escaping."""
        pr = PullRequest(title="Test PR", body='This has "quotes" in it')

        assert pr.formatted_body == 'This has \\"quotes\\" in it'


class TestGitBranch:
    """Test GitBranch model."""

    def test_git_branch_creation(self):
        """Test git branch creation."""
        branch = GitBranch(name="feature/test")

        assert branch.name == "feature/test"

    def test_is_valid_with_valid_name(self):
        """Test is_valid with valid branch name."""
        branch = GitBranch(name="feature/test")

        assert branch.is_valid is True

    def test_is_valid_with_empty_name(self):
        """Test is_valid with empty name."""
        branch = GitBranch(name="")

        assert branch.is_valid is False

    def test_is_valid_with_whitespace_name(self):
        """Test is_valid with whitespace only name."""
        branch = GitBranch(name="   ")

        assert branch.is_valid is False

    def test_is_valid_with_none_name(self):
        """Test is_valid with None name."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GitBranch(name=None)


class TestCommitType:
    """Test CommitType enum."""

    def test_commit_types_values(self):
        """Test commit type values."""
        assert CommitType.FEAT.value == "feat"
        assert CommitType.FIX.value == "fix"
        assert CommitType.DOCS.value == "docs"
        assert CommitType.STYLE.value == "style"
        assert CommitType.REFACTOR.value == "refactor"
        assert CommitType.TEST.value == "test"
        assert CommitType.CHORE.value == "chore"
