from __future__ import annotations

from typing import TYPE_CHECKING, Callable, TypeVar

from rich.console import RenderableType

from ai_cli.cli.ui.components.select.state import SelectState
from ai_cli.cli.ui.console import console

T = TypeVar("T")
R = TypeVar("R")

RenderFn = Callable[[SelectState[T]], RenderableType]
PlainRenderFn = Callable[[], RenderableType]

if TYPE_CHECKING:
    from prompt_toolkit.key_binding import KeyBindings

    BindKeysFn = Callable[[KeyBindings], None]
else:
    BindKeysFn = Callable[[object], None]


def run_prompt_toolkit(
    render: PlainRenderFn,
    bind_keys: BindKeysFn,
) -> R | None:
    try:
        from prompt_toolkit.application import Application
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.styles import Style
    except ImportError as exc:
        raise ImportError("prompt_toolkit not installed") from exc

    def _render() -> ANSI:
        console.begin_capture()
        console.print(render())
        content = console.end_capture()
        return ANSI(content)

    kb = KeyBindings()
    bind_keys(kb)

    style = Style.from_dict(
        {
            "header": "bold",
            "muted": "ansibrightblack",
        }
    )

    app = Application(
        layout=Layout(Window(FormattedTextControl(_render), wrap_lines=False)),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )
    return app.run()


def select_with_prompt_toolkit(
    state: SelectState[T],
    render: RenderFn[T],
) -> T | None:
    def _bind_keys(kb) -> None:
        @kb.add("up")
        def _move_up(event) -> None:
            state.move_up()
            event.app.invalidate()

        @kb.add("down")
        def _move_down(event) -> None:
            state.move_down()
            event.app.invalidate()

        @kb.add("enter")
        def _confirm(event) -> None:
            event.app.exit(result=state.confirm())

        @kb.add("escape")
        @kb.add("c-c")
        @kb.add("q")
        def _cancel(event) -> None:
            event.app.exit(result=None)

    return run_prompt_toolkit(
        render=lambda: render(state),
        bind_keys=_bind_keys,
    )
