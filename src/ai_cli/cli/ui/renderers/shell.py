from __future__ import annotations

from typing import Iterable

from prompt_toolkit.formatted_text import FormattedText, to_formatted_text

from ai_cli.cli.ui.components.theme import DEFAULT_THEME, Theme


def render_shell(
    *,
    title: str,
    context: str | None,
    body: str | FormattedText | Iterable[tuple[str, str]] | None,
    footer: str | None,
    theme: Theme = DEFAULT_THEME,
) -> FormattedText:
    parts: list[tuple[str, str]] = []
    parts.append(("class:header", title))
    if context:
        parts.append(("", "\n"))
        parts.append(("class:context", context))
    if body:
        parts.append(("", "\n\n"))
        parts.extend(_as_formatted_text(body))
    if footer:
        parts.append(("", "\n\n"))
        parts.append(("class:footer", footer))
    return FormattedText(parts)


def _as_formatted_text(
    content: str | FormattedText | Iterable[tuple[str, str]],
) -> list[tuple[str, str]]:
    formatted = to_formatted_text(content)
    return list(formatted)
