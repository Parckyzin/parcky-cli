from ai_cli.cli.ui.components.inputs.text import text_input


def test_text_input_editing_and_submit() -> None:
    result = text_input(
        title="Edit",
        context=None,
        label="Value",
        initial="",
        key_source=["a", "b", "left", "c", "right", "d", "enter"],
    )
    assert result == "acbd"


def test_text_input_parse_error_then_fix() -> None:
    def _parse(raw: str) -> int:
        return int(raw)

    result = text_input(
        title="Number",
        context=None,
        label="Value",
        initial="",
        parse=_parse,
        key_source=["a", "enter", "backspace", "4", "enter"],
    )
    assert result == 4


def test_text_input_cancel() -> None:
    result = text_input(
        title="Cancel",
        context=None,
        label="Value",
        initial="",
        key_source=["esc"],
    )
    assert result is None
