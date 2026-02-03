from __future__ import annotations

from collections.abc import Iterable

from ai_cli.cli.ui.components.inputs.text import text_input


def numeric_input(
    *,
    title: str,
    context: str | None,
    label: str,
    current_value: int | None,
    min_value: int,
    max_value: int | None = None,
    key_source: Iterable[str] | None = None,
) -> int | None:
    initial = str(current_value) if current_value is not None else ""
    resolved_context = context
    if resolved_context is None and current_value is not None:
        resolved_context = f"Current: {current_value}"

    def _parse(raw: str) -> int:
        value = int(raw.strip())
        return value

    def _validate(value: int) -> str | None:
        if value < min_value:
            return f"Enter a number >= {min_value}."
        if max_value is not None and value > max_value:
            return f"Enter a number <= {max_value}."
        return None

    return text_input(
        title=title,
        context=resolved_context,
        label=label,
        initial=initial,
        parse=_parse,
        validate=_validate,
        key_source=key_source,
    )
