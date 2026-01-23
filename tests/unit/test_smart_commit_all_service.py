"""
Unit tests for SmartCommitAllService.
"""

from unittest.mock import Mock, patch

from ai_cli.core.models import FileChange, GitDiff
from ai_cli.services.smart_commit_all_service import SmartCommitAllService


def _build_service(changes_sequence):
    git_repo = Mock()
    ai_service = Mock()

    git_repo.get_all_changes.side_effect = changes_sequence
    git_repo.get_diff_for_files.return_value = GitDiff(
        content="diff", is_truncated=False
    )
    ai_service.generate_text.return_value = (
        "GROUP: src/utils.py, src/app.py\nGROUP: src/test_app.py"
    )
    ai_service.generate_commit_message.return_value = "feat: update files"

    return SmartCommitAllService(git_repo=git_repo, ai_service=ai_service), git_repo


def test_plan_is_deterministic_across_input_order():
    changes_a = [
        FileChange(path="src/utils.py", status="M"),
        FileChange(path="src/app.py", status="M"),
        FileChange(path="src/test_app.py", status="M"),
    ]
    changes_b = [
        FileChange(path="src/test_app.py", status="M"),
        FileChange(path="src/app.py", status="M"),
        FileChange(path="src/utils.py", status="M"),
    ]

    service, _ = _build_service([changes_a, changes_b])

    plan_first = service.plan_smart_commit_all()
    plan_second = service.plan_smart_commit_all()

    groups_first = [group.file_paths for group in plan_first.groups]
    groups_second = [group.file_paths for group in plan_second.groups]

    assert groups_first == groups_second


def test_execute_dry_run_skips_git_mutations():
    changes = [
        FileChange(path="src/app.py", status="M"),
        FileChange(path="src/test_app.py", status="M"),
    ]
    service, git_repo = _build_service([changes])

    plan = service.plan_smart_commit_all()
    result = service.execute_smart_commit_all(dry_run=True, plan=plan)

    assert result.dry_run is True
    assert all(r.status == "planned" for r in result.commit_results)
    git_repo.unstage_all.assert_not_called()
    git_repo.stage_files.assert_not_called()
    git_repo.commit.assert_not_called()
    git_repo.push.assert_not_called()


def test_plan_with_multiple_groups():
    changes = [
        FileChange(path="src/utils.py", status="M"),
        FileChange(path="src/app.py", status="M"),
        FileChange(path="src/test_app.py", status="M"),
    ]
    service, _ = _build_service([changes])

    plan = service.plan_smart_commit_all()

    assert len(plan.groups) == 2
    assert len(plan.commit_results) == 2
    assert any(group.file_count > 1 for group in plan.groups)


def test_generate_commit_message_uses_pipeline():
    changes = [
        FileChange(path="src/app.py", status="M"),
    ]
    service, _ = _build_service([changes])
    group = service.plan_smart_commit_all().groups[0]

    with patch(
        "ai_cli.pipelines.commit_message.build_commit_context",
        return_value="context",
    ) as build_context:
        service.generate_commit_message_for_group(group)

    build_context.assert_called_once_with(group.diff, group.file_paths)
