from __future__ import annotations

from typing import TYPE_CHECKING, Callable, TypeVar

from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme, prompt_toolkit_style

T = TypeVar("T")
R = TypeVar("R")

if TYPE_CHECKING:
    from ai_cli.cli.ui.components.select.state import SelectState

RenderFn = Callable[
    ["SelectState[T]"], str | list[tuple[str, str]]
]
PlainRenderFn = Callable[[], str | list[tuple[str, str]]]
OverlayRenderFn = Callable[[], str | list[tuple[str, str]] | None]

if TYPE_CHECKING:
    from prompt_toolkit.key_binding import KeyBindings

    BindKeysFn = Callable[[KeyBindings], None]
else:
    BindKeysFn = Callable[[object], None]


def run_prompt_toolkit(
    render: PlainRenderFn,
    bind_keys: BindKeysFn,
    theme: Theme = DEFAULT_THEME,
) -> R | None:
    try:
        from prompt_toolkit.application import Application
        from prompt_toolkit.formatted_text import to_formatted_text
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.styles import Style
    except ImportError as exc:
        raise ImportError("prompt_toolkit not installed") from exc

    def _render():
        return _to_formatted_text(render(), to_formatted_text)

    kb = KeyBindings()
    bind_keys(kb)

    style = Style.from_dict(prompt_toolkit_style(theme))

    app = Application(
        layout=Layout(Window(FormattedTextControl(_render), wrap_lines=False)),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )
    return app.run()


def run_prompt_toolkit_screen(
    render_base: PlainRenderFn,
    render_overlay: OverlayRenderFn | None,
    bind_keys: BindKeysFn,
    bind_overlay_keys: BindKeysFn | None = None,
    theme: Theme = DEFAULT_THEME,
) -> R | None:
    try:
        from prompt_toolkit.application import Application
        from prompt_toolkit.formatted_text import FormattedText, to_formatted_text
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import Float, FloatContainer, Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.styles import Style
    except ImportError as exc:
        raise ImportError("prompt_toolkit not installed") from exc

    def _render_base() -> FormattedText:
        return _to_formatted_text(render_base(), to_formatted_text)

    def _render_overlay() -> FormattedText:
        if render_overlay is None:
            return FormattedText([])
        overlay = render_overlay()
        if overlay is None:
            return FormattedText([])
        return _to_formatted_text(overlay, to_formatted_text)

    kb = KeyBindings()
    bind_keys(kb)
    if bind_overlay_keys is not None:
        bind_overlay_keys(kb)

    container = FloatContainer(
        content=Window(FormattedTextControl(_render_base), wrap_lines=False),
        floats=(
            []
            if render_overlay is None
            else [Float(content=Window(FormattedTextControl(_render_overlay)))]
        ),
    )

    style = Style.from_dict(prompt_toolkit_style(theme))

    app = Application(
        layout=Layout(container),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )
    return app.run()


def _to_formatted_text(value, to_formatted_text) -> FormattedText:
    try:
        return to_formatted_text(value)
    except Exception:
        return to_formatted_text(str(value))


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
