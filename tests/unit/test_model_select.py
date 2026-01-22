from ai_cli.cli.ui import model_select


def test_fallback_on_import_error(monkeypatch) -> None:
    def _raise_import(*_args, **_kwargs):
        raise ImportError("no prompt_toolkit")

    monkeypatch.setattr(model_select, "_select_with_prompt_toolkit", _raise_import)
    monkeypatch.setattr(model_select, "prompt", lambda _msg: "manual-model")

    selected: list[str] = []

    def _on_select(model: str) -> None:
        selected.append(model)

    model_select.interactive_model_select(["model-a"], "model-a", _on_select)
    assert selected == ["manual-model"]


def test_manual_selection_returns_value(monkeypatch) -> None:
    monkeypatch.setattr(model_select, "prompt", lambda _msg: "custom-model")

    selected: list[str] = []

    def _on_select(model: str) -> None:
        selected.append(model)

    model_select.interactive_model_select([], "model-a", _on_select)
    assert selected == ["custom-model"]
