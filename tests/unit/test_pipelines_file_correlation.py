from ai_cli.core.models import FileChange
from ai_cli.pipelines import file_correlation as file_correlation_pipeline


def test_parse_group_response_matches_paths_and_basenames():
    files = [
        FileChange(path="src/app.py", status="M"),
        FileChange(path="src/utils.py", status="M"),
    ]
    response = "GROUP: src/app.py, utils.py"

    groups = file_correlation_pipeline.parse_group_response(
        response, files, folder="src"
    )

    assert len(groups) == 1
    assert set(groups[0].file_paths) == {"src/app.py", "src/utils.py"}
