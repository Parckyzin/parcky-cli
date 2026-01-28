from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rich.console import Group, RenderableType
from rich.text import Text

from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme
from ai_cli.cli.ui.renderers.frame import render_frame

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
) -> RenderableType:
    icon, variant_style = _variant_tokens(variant, theme)
    title_text = f"{icon} {title}".strip()
    body_text = Text(body, style=theme.modal_body_style)
    actions_text = _render_actions(state, theme)

    return render_frame(
        title=title_text,
        body=Group(body_text, actions_text),
        variant=variant,
        theme=theme,
        align=True,
    )


def _render_actions(state: ModalState, theme: Theme) -> Text:
    text = Text()
    for idx, action in enumerate(state.actions):
        if idx:
            text.append("  ")
        is_selected = idx == state.index
        style = (
            theme.modal_action_selected_style
            if is_selected
            else theme.modal_action_style
        )
        text.append(action.label, style=style)
    return text


def _variant_tokens(variant: ModalVariant, theme: Theme) -> tuple[str, str]:
    if variant == "warn":
        return theme.modal_warn_icon, theme.modal_warn_style
    if variant == "error":
        return theme.modal_error_icon, theme.modal_error_style
    if variant == "success":
        return theme.modal_success_icon, theme.modal_success_style
    return theme.modal_info_icon, theme.modal_info_style
