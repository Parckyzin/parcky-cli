from __future__ import annotations

from dataclasses import dataclass


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

    modal_info_style: str = "cyan"
    modal_warn_style: str = "yellow"
    modal_error_style: str = "red"
    modal_success_style: str = "green"

    modal_info_icon: str = "ℹ"
    modal_warn_icon: str = "⚠"
    modal_error_icon: str = "✖"
    modal_success_icon: str = "✔"


DEFAULT_THEME = Theme()
