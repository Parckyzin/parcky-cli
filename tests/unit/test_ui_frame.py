from rich.console import Console
from rich.text import Text

from ai_cli.cli.ui.renderers.frame import render_frame


def test_render_frame_outputs_title_body_footer() -> None:
    renderable = render_frame(
        title="Frame Title",
        body=Text("Body text"),
        footer="Footer text",
    )
    console = Console(
        color_system=None, force_terminal=False, markup=False, record=True
    )
    console.print(renderable)
    output = console.export_text()
    assert "Frame Title" in output
    assert "Body text" in output
    assert "Footer text" in output
