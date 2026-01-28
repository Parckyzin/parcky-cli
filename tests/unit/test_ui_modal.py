from rich.console import Console

from ai_cli.cli.ui.components.modal import confirm
from ai_cli.cli.ui.renderers.modal import ModalAction, ModalState, render_modal


def test_confirm_returns_true_on_enter() -> None:
    result = confirm(
        title="Confirm?",
        body="Proceed",
        key_source=["enter"],
    )
    assert result is True


def test_confirm_returns_false_on_cancel() -> None:
    result = confirm(
        title="Confirm?",
        body="Proceed",
        key_source=["esc"],
    )
    assert result is False


def test_render_modal_outputs_title_body_and_actions() -> None:
    state = ModalState(
        actions=[
            ModalAction(label="Yes", value="yes"),
            ModalAction(label="No", value="no"),
        ],
        index=0,
    )
    panel = render_modal(state, title="Title", body="Body")
    console = Console(
        color_system=None, force_terminal=False, markup=False, record=True
    )
    console.print(panel)
    text = console.export_text()
    assert "Title" in text
    assert "Body" in text
    assert "Yes" in text
    assert "No" in text
