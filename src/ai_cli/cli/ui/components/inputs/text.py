from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, TypeVar

from prompt_toolkit.formatted_text import FormattedText

from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme
from ai_cli.cli.ui.drivers.prompt_toolkit import run_prompt_toolkit
from ai_cli.cli.ui.renderers.shell import render_shell

T = TypeVar("T")


@dataclass
class TextInputState:
    title: str
    context: str | None
    label: str
    buffer: str
    cursor: int
    error: str | None


def text_input(
    *,
    title: str,
    context: str | None,
    label: str,
    initial: str = "",
    parse: Callable[[str], T] | None = None,
    validate: Callable[[T], str | None] | None = None,
    theme: Theme = DEFAULT_THEME,
    key_source: Iterable[str] | None = None,
) -> T | None:
    state = TextInputState(
        title=title,
        context=context,
        label=label,
        buffer=initial,
        cursor=len(initial),
        error=None,
    )

    if key_source is not None:
        return _run_from_key_source(state, parse, validate, key_source)

    def _render() -> FormattedText:
        return _render_state(state, theme)

    def _bind_keys(kb) -> None:
        @kb.add("left")
        def _left(event) -> None:
            if state.cursor > 0:
                state.cursor -= 1
                event.app.invalidate()

        @kb.add("right")
        def _right(event) -> None:
            if state.cursor < len(state.buffer):
                state.cursor += 1
                event.app.invalidate()

        @kb.add("home")
        def _home(event) -> None:
            state.cursor = 0
            event.app.invalidate()

        @kb.add("end")
        def _end(event) -> None:
            state.cursor = len(state.buffer)
            event.app.invalidate()

        @kb.add("backspace")
        @kb.add("c-h")
        def _backspace(event) -> None:
            if state.cursor <= 0:
                return
            state.buffer = (
                state.buffer[: state.cursor - 1] + state.buffer[state.cursor :]
            )
            state.cursor -= 1
            state.error = None
            event.app.invalidate()

        @kb.add("delete")
        def _delete(event) -> None:
            if state.cursor >= len(state.buffer):
                return
            state.buffer = (
                state.buffer[: state.cursor] + state.buffer[state.cursor + 1 :]
            )
            state.error = None
            event.app.invalidate()

        @kb.add("enter")
        def _enter(event) -> None:
            result, error = _submit(state, parse, validate)
            if error:
                state.error = error
                event.app.invalidate()
                return
            event.app.exit(result=result)

        @kb.add("escape")
        @kb.add("c-c")
        def _cancel(event) -> None:
            event.app.exit(result=None)

        @kb.add("<any>")
        def _type(event) -> None:
            data = event.data
            if not data or not data.isprintable():
                return
            if data in {"\n", "\r"}:
                return
            state.buffer = (
                state.buffer[: state.cursor] + data + state.buffer[state.cursor :]
            )
            state.cursor += 1
            state.error = None
            event.app.invalidate()

    result = run_prompt_toolkit(render=_render, bind_keys=_bind_keys, theme=theme)
    if isinstance(result, TextInputResult):
        return result.value
    return None


@dataclass(frozen=True)
class TextInputResult:
    value: T


def _submit(
    state: TextInputState,
    parse: Callable[[str], T] | None,
    validate: Callable[[T], str | None] | None,
) -> tuple[TextInputResult | None, str | None]:
    raw = state.buffer
    if parse is None:
        value: Any = raw
    else:
        try:
            value = parse(raw)
        except ValueError as exc:
            return None, str(exc) or "Invalid input."
    if validate is not None:
        error = validate(value)
        if error:
            return None, error
    return TextInputResult(value=value), None


def _run_from_key_source(
    state: TextInputState,
    parse: Callable[[str], T] | None,
    validate: Callable[[T], str | None] | None,
    key_source: Iterable[str],
) -> T | None:
    for key in key_source:
        result, done = _apply_key(state, key, parse, validate)
        if done:
            return result
    return None


def _apply_key(
    state: TextInputState,
    key: str,
    parse: Callable[[str], T] | None,
    validate: Callable[[T], str | None] | None,
) -> tuple[T | None, bool]:
    if key in {"esc", "c-c"}:
        return None, True
    if key == "left":
        if state.cursor > 0:
            state.cursor -= 1
        return None, False
    if key == "right":
        if state.cursor < len(state.buffer):
            state.cursor += 1
        return None, False
    if key == "home":
        state.cursor = 0
        return None, False
    if key == "end":
        state.cursor = len(state.buffer)
        return None, False
    if key in {"backspace", "c-h"}:
        if state.cursor > 0:
            state.buffer = (
                state.buffer[: state.cursor - 1] + state.buffer[state.cursor :]
            )
            state.cursor -= 1
        return None, False
    if key == "delete":
        if state.cursor < len(state.buffer):
            state.buffer = (
                state.buffer[: state.cursor] + state.buffer[state.cursor + 1 :]
            )
        return None, False
    if key == "enter":
        result, error = _submit(state, parse, validate)
        if error:
            state.error = error
            return None, False
        return result.value if result else None, True
    if key.isprintable() and len(key) == 1:
        state.buffer = state.buffer[: state.cursor] + key + state.buffer[state.cursor :]
        state.cursor += 1
        state.error = None
    return None, False


def _render_state(state: TextInputState, theme: Theme) -> FormattedText:
    input_line = _render_input_line(state)
    body: list[tuple[str, str]] = []
    body.append(("class:muted", state.label))
    body.append(("", "\n"))
    body.extend(input_line)
    if state.error:
        body.append(("", "\n"))
        body.append(("class:error", state.error))
    return render_shell(
        title=state.title,
        context=state.context,
        body=body,
        footer="Enter submit • Esc cancel",
        theme=theme,
    )


def _render_input_line(state: TextInputState) -> list[tuple[str, str]]:
    before = state.buffer[: state.cursor]
    cursor = "|" if state.cursor <= len(state.buffer) else "|"
    after = state.buffer[state.cursor :]
    parts: list[tuple[str, str]] = []
    parts.append(("class:accent", before))
    parts.append(("class:selected", cursor))
    parts.append(("class:accent", after))
    return parts
