from __future__ import annotations

import sys
import types

from rich.text import Text

from ai_cli.cli.ui.drivers import prompt_toolkit as driver


def _install_prompt_toolkit_stubs(monkeypatch) -> None:
    class FakeFormattedText(list):
        pass

    class FakeKeyBindings:
        def add(self, *_keys):
            def _decorator(func):
                return func

            return _decorator

    class FakeFormattedTextControl:
        def __init__(self, text):
            self.text = text

    class FakeWindow:
        def __init__(self, content, **_kwargs):
            self.content = content

    class FakeFloat:
        def __init__(self, content):
            self.content = content

    class FakeFloatContainer:
        def __init__(self, content, floats=None):
            self.content = content
            self.floats = floats or []

    class FakeLayout:
        def __init__(self, container):
            self.container = container

    class FakeStyle:
        @staticmethod
        def from_dict(_data):
            return FakeStyle()

    class FakeApplication:
        def __init__(self, layout, _key_bindings, _style, _full_screen):
            self.layout = layout

        def run(self):
            base_control = self.layout.container.content.content
            base_control.text()
            for fl in self.layout.container.floats:
                fl.content.content.text()
            return "ok"

    modules = {
        "prompt_toolkit.application": types.SimpleNamespace(
            Application=FakeApplication
        ),
        "prompt_toolkit.formatted_text": types.SimpleNamespace(
            FormattedText=FakeFormattedText,
            to_formatted_text=lambda text: text,
        ),
        "prompt_toolkit.key_binding": types.SimpleNamespace(
            KeyBindings=FakeKeyBindings
        ),
        "prompt_toolkit.layout": types.SimpleNamespace(Layout=FakeLayout),
        "prompt_toolkit.layout.containers": types.SimpleNamespace(
            Float=FakeFloat, FloatContainer=FakeFloatContainer, Window=FakeWindow
        ),
        "prompt_toolkit.layout.controls": types.SimpleNamespace(
            FormattedTextControl=FakeFormattedTextControl
        ),
        "prompt_toolkit.styles": types.SimpleNamespace(Style=FakeStyle),
    }

    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)


def test_run_prompt_toolkit_screen_renders_base_and_overlay(monkeypatch) -> None:
    calls = {"base": 0, "overlay": 0}
    _install_prompt_toolkit_stubs(monkeypatch)

    def _base():
        calls["base"] += 1
        return Text("base")

    def _overlay():
        calls["overlay"] += 1
        return Text("overlay")

    result = driver.run_prompt_toolkit_screen(
        render_base=_base,
        render_overlay=_overlay,
        bind_keys=lambda _kb: None,
        bind_overlay_keys=lambda _kb: None,
    )

    assert result == "ok"
    assert calls["base"] == 1
    assert calls["overlay"] == 1


def test_run_prompt_toolkit_screen_without_overlay(monkeypatch) -> None:
    calls = {"base": 0}
    _install_prompt_toolkit_stubs(monkeypatch)

    def _base():
        calls["base"] += 1
        return Text("base")

    result = driver.run_prompt_toolkit_screen(
        render_base=_base,
        render_overlay=None,
        bind_keys=lambda _kb: None,
    )

    assert result == "ok"
    assert calls["base"] == 1
