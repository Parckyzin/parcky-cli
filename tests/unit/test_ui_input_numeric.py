from ai_cli.cli.ui.components.inputs.numeric import numeric_input


def test_numeric_input_min_validation() -> None:
    result = numeric_input(
        title="Number",
        context=None,
        label="Value",
        current_value=None,
        min_value=10,
        max_value=None,
        key_source=["5", "enter", "backspace", "1", "0", "enter"],
    )
    assert result == 10


def test_numeric_input_accepts_value() -> None:
    result = numeric_input(
        title="Number",
        context=None,
        label="Value",
        current_value=None,
        min_value=1,
        max_value=None,
        key_source=["4", "2", "enter"],
    )
    assert result == 42
