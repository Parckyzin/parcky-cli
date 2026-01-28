from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme
from ai_cli.cli.ui.drivers.prompt_toolkit import run_prompt_toolkit
from ai_cli.cli.ui.renderers.modal import (
    ModalAction,
    ModalState,
    ModalVariant,
    render_modal,
)

ModalKey = Literal["enter", "esc", "q", "left", "right", "c-c"]


@dataclass(frozen=True)
class ModalResult:
    value: str | None
    cancelled: bool


def confirm(
    *,
    title: str,
    body: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    variant: ModalVariant = "info",
    theme: Theme = DEFAULT_THEME,
    key_source: Iterable[ModalKey] | None = None,
) -> bool:
    result = modal(
        title=title,
        body=body,
        actions=[
            ModalAction(label=confirm_label, value="confirm"),
            ModalAction(label=cancel_label, value="cancel"),
        ],
        variant=variant,
        theme=theme,
        key_source=key_source,
    )
    return result.value == "confirm" and not result.cancelled


def modal(
    *,
    title: str,
    body: str,
    actions: list[ModalAction],
    variant: ModalVariant = "info",
    theme: Theme = DEFAULT_THEME,
    key_source: Iterable[ModalKey] | None = None,
) -> ModalResult:
    state = ModalState(actions=actions, index=0)
    if key_source is not None:
        return _run_from_key_source(state, key_source)

    def _bind_keys(kb) -> None:
        @kb.add("left")
        def _left(event) -> None:
            _move_index(state, -1)
            event.app.invalidate()

        @kb.add("right")
        def _right(event) -> None:
            _move_index(state, 1)
            event.app.invalidate()

        @kb.add("enter")
        def _confirm(event) -> None:
            event.app.exit(result=ModalResult(state.actions[state.index].value, False))

        @kb.add("escape")
        @kb.add("q")
        @kb.add("c-c")
        def _cancel(event) -> None:
            event.app.exit(result=ModalResult(None, True))

    result = run_prompt_toolkit(
        render=lambda: render_modal(
            state, title=title, body=body, variant=variant, theme=theme
        ),
        bind_keys=_bind_keys,
    )
    if isinstance(result, ModalResult):
        return result
    return ModalResult(None, True)


def _run_from_key_source(
    state: ModalState,
    key_source: Iterable[ModalKey],
) -> ModalResult:
    for key in key_source:
        result = handle_key(state, key)
        if result is not None:
            return result
    return ModalResult(None, True)


def handle_key(state: ModalState, key: ModalKey) -> ModalResult | None:
    if key in {"esc", "q", "c-c"}:
        return ModalResult(None, True)
    if key == "enter":
        return ModalResult(state.actions[state.index].value, False)
    if key == "left":
        _move_index(state, -1)
    elif key == "right":
        _move_index(state, 1)
    return None


def _move_index(state: ModalState, delta: int) -> None:
    if not state.actions:
        state.index = 0
        return
    state.index = (state.index + delta) % len(state.actions)
