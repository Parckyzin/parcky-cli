from __future__ import annotations

from typing import Literal

from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme

FrameVariant = Literal["default", "info", "warn", "error", "success"]

SELECT_FOOTER = "↑/↓ move • Enter select • Esc cancel"
SELECT_FILTER_FOOTER = "↑/↓ move • Enter select • Esc cancel • type to filter"
MODEL_FILTER_FOOTER = "↑/↓ move • Enter select • Esc cancel • '/' filter • Ctrl+U clear"
TEXT_FALLBACK_FOOTER = "Enter number or blank to cancel"
VALUE_INPUT_FOOTER = "Enter value • Ctrl+C cancel"


def render_frame(
    *,
    title: str,
    body: RenderableType,
    footer: RenderableType | None = None,
    variant: FrameVariant = "default",
    theme: Theme = DEFAULT_THEME,
    align: bool = False,
) -> RenderableType:
    variant_style = _variant_style(variant, theme)
    border_style = variant_style or theme.frame_border_style
    title_style = _combine_styles(theme.frame_title_style, variant_style)
    title_text = Text(title, style=title_style)

    if footer is None:
        content = body
    else:
        footer_renderable = (
            Text(footer, style=theme.frame_footer_style)
            if isinstance(footer, str)
            else footer
        )
        content = Group(body, footer_renderable)

    panel = Panel(
        content,
        border_style=border_style,
        padding=theme.frame_padding,
        title=title_text,
    )
    if not align:
        return panel
    return Align.center(panel, vertical="middle")


def _variant_style(variant: FrameVariant, theme: Theme) -> str:
    if variant == "info":
        return theme.frame_info_style
    if variant == "warn":
        return theme.frame_warn_style
    if variant == "error":
        return theme.frame_error_style
    if variant == "success":
        return theme.frame_success_style
    return ""


def _combine_styles(*styles: str) -> str:
    return " ".join(style for style in styles if style)
