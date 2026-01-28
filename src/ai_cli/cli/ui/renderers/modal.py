from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

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
) -> RenderableType:
    icon, variant_style = _variant_tokens(variant, theme)
    title_style = _combine_styles(variant_style, theme.modal_title_style)

    title_text = Text(f"{icon} {title}".strip(), style=title_style)
    body_text = Text(body, style=theme.modal_body_style)
    actions_text = _render_actions(state, theme)

    panel = Panel(
        Group(title_text, body_text, actions_text),
        border_style=variant_style or theme.modal_border_style,
        padding=(1, 2),
    )
    return Align.center(panel, vertical="middle")


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


def _combine_styles(*styles: str) -> str:
    return " ".join(style for style in styles if style)
