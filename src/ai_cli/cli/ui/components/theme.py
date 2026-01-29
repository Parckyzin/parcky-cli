from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field


@dataclass(frozen=True)
class Theme:
    """Visual tokens for CLI UI components."""

    header_style: str = "bold"
    muted_style: str = "dim"
    selected_style: str = "reverse"
    accent_style: str = "white"
    disabled_style: str = "dim"
    current_style: str = "purple"
    selected_row_style: str = "dim"
    marker_style: str = "dim"

    selected_marker: str = ">"
    current_marker: str = "●"
    current_label: str = "current"
    disabled_marker: str = "x"

    empty_label: str = "No options available"

    modal_border_style: str = "dim"
    modal_title_style: str = "bold"
    modal_body_style: str = ""
    modal_action_style: str = "dim"
    modal_action_selected_style: str = "reverse"

    modal_info_style: str = "purple"
    modal_warn_style: str = "yellow"
    modal_error_style: str = "red"
    modal_success_style: str = "green"

    modal_info_icon: str = "ℹ"
    modal_warn_icon: str = "⚠"
    modal_error_icon: str = "✖"
    modal_success_icon: str = "✔"

    ptk_header_style: str = "bold"
    ptk_context_style: str = "ansibrightblack"
    ptk_footer_style: str = "ansibrightblack"
    ptk_selected_style: str = "reverse"
    ptk_selected_row_style: str = "reverse"
    ptk_current_style: str = "ansipurple"
    ptk_disabled_style: str = "ansibrightblack"
    ptk_muted_style: str = "ansibrightblack"
    ptk_accent_style: str = ""
    ptk_marker_style: str = "ansibrightblack"
    ptk_error_style: str = "ansired"
    ptk_warning_style: str = "ansiyellow"
    ptk_styles: dict[str, str] = field(default_factory=dict)

    frame_border_style: str = "dim"
    frame_title_style: str = "bold"
    frame_footer_style: str = "dim"
    frame_padding: tuple[int, int] = (1, 2)

    frame_info_style: str = "purple"
    frame_warn_style: str = "yellow"
    frame_error_style: str = "red"
    frame_success_style: str = "green"


DEFAULT_THEME = Theme()


def prompt_toolkit_style(theme: Theme) -> dict[str, str]:
    base = {
        "header": theme.ptk_header_style,
        "context": theme.ptk_context_style,
        "footer": theme.ptk_footer_style,
        "selected": theme.ptk_selected_style,
        "selected_row": theme.ptk_selected_row_style,
        "current": theme.ptk_current_style,
        "disabled": theme.ptk_disabled_style,
        "muted": theme.ptk_muted_style,
        "accent": theme.ptk_accent_style,
        "marker": theme.ptk_marker_style,
        "error": theme.ptk_error_style,
        "warning": theme.ptk_warning_style,
    }
    if theme.ptk_styles:
        for key, value in theme.ptk_styles.items():
            if key.startswith("class:"):
                base[key.split("class:", 1)[1]] = value
            else:
                base[key] = value
    return base
