from rich.console import Console
from rich.text import Text

from ai_cli.cli.ui.components import SelectOption, SelectState, Theme, handle_key
from ai_cli.cli.ui.renderers.select_table import (
    TableColumnSpec,
    _compute_row_styles,
    render_table,
)


def test_navigation_clamps():
    options = [
        SelectOption(value="a", label="A"),
        SelectOption(value="b", label="B"),
    ]
    state = SelectState.from_options(options)
    assert state.index == 0

    state.move_up()
    assert state.index == 0

    state.move_down()
    assert state.index == 1

    state.move_down()
    assert state.index == 1


def test_skips_disabled_items():
    options = [
        SelectOption(value="a", label="A", disabled=True),
        SelectOption(value="b", label="B"),
        SelectOption(value="c", label="C", disabled=True),
        SelectOption(value="d", label="D"),
    ]
    state = SelectState.from_options(options)
    assert state.index == 1

    state.move_down()
    assert state.index == 3

    state.move_up()
    assert state.index == 1


def test_confirm_returns_selected_value():
    options = [
        SelectOption(value="a", label="A"),
        SelectOption(value="b", label="B"),
    ]
    state = SelectState.from_options(options)
    state.move_down()
    assert state.confirm() == "b"


def test_cancel_returns_none():
    options = [
        SelectOption(value="a", label="A"),
        SelectOption(value="b", label="B"),
    ]
    state = SelectState.from_options(options)
    result = handle_key(state, "esc")
    assert result.action == "cancel"
    assert result.value is None


def test_render_table_does_not_emit_ansi():
    options = [
        SelectOption(value="a", label="Option A"),
        SelectOption(value="b", label="Option B"),
    ]
    state = SelectState.from_options(options)
    table = render_table(state, title="Select", show_index=True)
    console = Console(
        color_system=None, force_terminal=False, markup=False, record=True
    )
    console.print(table)
    text = console.export_text()
    assert "\x1b" not in text


def test_render_table_strips_ansi_input():
    options = [
        SelectOption(value="a", label="A\x1b[36m"),
        SelectOption(value="b", label="B\x1b[0m"),
    ]
    state = SelectState.from_options(options)
    table = render_table(state)
    console = Console(
        color_system=None, force_terminal=False, markup=False, record=True
    )
    console.print(table)
    text = console.export_text()
    assert "\x1b" not in text


def test_render_table_marks_current_status():
    options = [
        SelectOption(value="a", label="Option A", is_current=True),
        SelectOption(value="b", label="Option B"),
    ]
    state = SelectState.from_options(options)
    table = render_table(state)
    console = Console(
        color_system=None, force_terminal=False, markup=False, record=True
    )
    console.print(table)
    text = console.export_text()
    assert "● current" in text


def test_selected_label_uses_selected_style():
    theme = Theme(selected_style="bold", selected_row_style="dim", marker_style="dim")
    options = [
        SelectOption(value="a", label="Option A"),
        SelectOption(value="b", label="Option B"),
    ]
    state = SelectState.from_options(options)
    state.index = 1
    table = render_table(state, theme=theme)
    label_cell = table.columns[1]._cells[1]
    assert isinstance(label_cell, Text)
    assert label_cell.style == theme.selected_style


def test_row_style_priority():
    theme = Theme()
    state = SelectState.from_options(
        [
            SelectOption(value="a", label="A", disabled=True, is_current=True),
            SelectOption(value="b", label="B", is_current=True),
            SelectOption(value="c", label="C"),
        ]
    )
    state.index = 1
    styles_disabled = _compute_row_styles(state.options[0], state, 0, theme)
    styles_selected = _compute_row_styles(state.options[1], state, 1, theme)
    styles_normal = _compute_row_styles(state.options[2], state, 2, theme)
    assert styles_disabled.label_style == theme.disabled_style
    assert styles_selected.label_style == theme.selected_style
    assert styles_normal.label_style == theme.accent_style


def test_custom_columns_shape():
    options = [
        SelectOption(value="a", label="Option A", is_current=True),
    ]
    state = SelectState.from_options(options)
    columns = [
        TableColumnSpec(
            header="Option",
            render=lambda opt, _state, _idx, styles, _theme: Text(
                opt.label, style=styles.label_style
            ),
        ),
        TableColumnSpec(
            header="Status",
            render=lambda opt, _state, _idx, styles, theme: Text(
                f"{theme.current_marker} {theme.current_label}"
                if opt.is_current
                else "",
                style=styles.status_style,
            ),
        ),
    ]
    table = render_table(state, columns=columns)
    assert len(table.columns) == 2


def test_default_columns_shape():
    options = [SelectOption(value="a", label="Option A")]
    state = SelectState.from_options(options)
    table = render_table(state)
    assert len(table.columns) == 4
