from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class SelectOption(Generic[T]):
    value: T
    label: str
    description: str | None = None
    disabled: bool = False
    is_current: bool = False


@dataclass
class SelectState(Generic[T]):
    options: list[SelectOption[T]]
    index: int | None

    @classmethod
    def from_options(cls, options: Sequence[SelectOption[T]]) -> SelectState[T]:
        option_list = list(options)
        index = _first_enabled_index(option_list)
        return cls(options=option_list, index=index)

    def current(self) -> SelectOption[T] | None:
        if self.index is None:
            return None
        if 0 <= self.index < len(self.options):
            return self.options[self.index]
        return None

    def move_up(self) -> None:
        self._move(-1)

    def move_down(self) -> None:
        self._move(1)

    def confirm(self) -> T | None:
        option = self.current()
        if option is None or option.disabled:
            return None
        return option.value

    def _move(self, direction: int) -> None:
        if self.index is None or not self.options:
            return
        next_index = _next_enabled_index(self.options, self.index, direction)
        self.index = next_index


def _first_enabled_index(options: Sequence[SelectOption[T]]) -> int | None:
    for idx, option in enumerate(options):
        if not option.disabled:
            return idx
    return None


def _next_enabled_index(
    options: Sequence[SelectOption[T]],
    current: int,
    direction: int,
) -> int:
    if direction == 0:
        return current
    step = 1 if direction > 0 else -1
    candidate = current + step
    while 0 <= candidate < len(options):
        if not options[candidate].disabled:
            return candidate
        candidate += step
    return current
