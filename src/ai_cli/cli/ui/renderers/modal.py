from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from prompt_toolkit.formatted_text import FormattedText

from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme

ModalVariant = Literal["info", "warn", "error", "success"]


@dataclass(frozen=True)
class ModalAction:
    label: str
    value: str


@dataclass
class ModalState:
    actions: list[ModalAction]
    index: int = 0


def render_modal(
        state: ModalState,
        *,
        title: str,
        body: str,
        variant: ModalVariant = "info",
        theme: Theme = DEFAULT_THEME,
) -> FormattedText:
    icon, _variant_class = _variant_tokens(variant, theme)
    title_text = f"{icon} {title}".strip()

    parts: list[tuple[str, str]] = []
    parts.append(("class:header", title_text))
    parts.append(("", "\n\n"))

    if body:
        parts.append(("class:accent", body))
        parts.append(("", "\n\n"))

    parts.extend(_render_actions(state))
    return FormattedText(parts)


def _render_actions(state: ModalState) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    for idx, action in enumerate(state.actions):
        if idx:
            parts.append(("", "  "))
        style = "class:selected_row" if idx == state.index else "class:muted"
        parts.append((style, f"[ {action.label} ]"))
    return parts


def _variant_tokens(variant: ModalVariant, theme: Theme) -> tuple[str, str]:
    if variant == "warn":
        return theme.modal_warn_icon, "class:warning"
    if variant == "error":
        return theme.modal_error_icon, "class:error"
    if variant == "success":
        return theme.modal_success_icon, "class:current"
    return theme.modal_info_icon, "class:accent"
