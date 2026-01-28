from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

from .state import SelectState

T = TypeVar("T")

KeyAction = Literal["select", "cancel", "none"]


@dataclass(frozen=True)
class SelectResult(Generic[T]):
    action: KeyAction
    value: T | None = None


def handle_key(state: SelectState[T], key: str) -> SelectResult[T]:
    key_lower = key.lower()
    if key_lower in {"up", "k"}:
        state.move_up()
        return SelectResult(action="none")
    if key_lower in {"down", "j"}:
        state.move_down()
        return SelectResult(action="none")
    if key_lower in {"enter", "return"}:
        return SelectResult(action="select", value=state.confirm())
    if key_lower in {"esc", "escape", "q"}:
        return SelectResult(action="cancel")
    return SelectResult(action="none")
