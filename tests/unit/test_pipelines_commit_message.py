from ai_cli.core.models import GitDiff
from ai_cli.pipelines import commit_message as commit_message_pipeline


def test_build_commit_context_is_deterministic_for_file_order():
    diff = GitDiff(content="diff --git a/a.txt b/a.txt\n+line", is_truncated=False)
    files_a = ["b.txt", "a.txt"]
    files_b = ["a.txt", "b.txt"]

    context_a = commit_message_pipeline.build_commit_context(diff, files_a)
    context_b = commit_message_pipeline.build_commit_context(diff, files_b)

    assert context_a == context_b


def test_build_commit_context_truncates_examples_with_header():
    diff_content = "\n".join([f"+line{i}" for i in range(5)])
    diff = GitDiff(content=diff_content, is_truncated=False)

    context = commit_message_pipeline.build_commit_context(
        diff, ["a.txt"], max_example_lines=2
    )

    assert context.startswith("SUMMARY")
    assert "+line0" in context
    assert "+line1" in context
    assert "+line2" not in context
    assert "Diff examples truncated to 2 lines." in context
