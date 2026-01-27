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


DEFAULT_THEME = Theme()
