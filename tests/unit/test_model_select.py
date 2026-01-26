from ai_cli.cli.ui import model_select


def test_provider_change_refreshes_models(monkeypatch) -> None:
    calls: list[list[str]] = []
    results = [
        model_select.SelectionResult(action="change_provider"),
        model_select.SelectionResult(action="model", value="new-model"),
    ]

    def _fake_select(models, current_model, show_change_provider):
        calls.append(models)
        return results.pop(0)

    monkeypatch.setattr(model_select, "_select_with_prompt_toolkit", _fake_select)
    monkeypatch.setattr(
        model_select, "select_provider", lambda current=None: "openai"
    )

    changed: list[str] = []

    def _on_change_provider(provider: str):
        changed.append(provider)
        return ["new-model", "other"], ""

    selected: list[str] = []

    def _on_select(model: str) -> None:
        selected.append(model)

    model_select.interactive_model_select(
        ["old-model"],
        "old-model",
        _on_select,
        current_provider="google",
        on_change_provider=_on_change_provider,
    )

    assert changed == ["openai"]
    assert selected == ["new-model"]
    assert calls[0] == ["old-model"]
    assert calls[1] == ["new-model", "other"]


def test_provider_change_cancel_keeps_state(monkeypatch) -> None:
    results = [
        model_select.SelectionResult(action="change_provider"),
        model_select.SelectionResult(action="cancel"),
    ]

    def _fake_select(_models, _current_model, _show_change_provider):
        return results.pop(0)

    monkeypatch.setattr(model_select, "_select_with_prompt_toolkit", _fake_select)
    monkeypatch.setattr(model_select, "select_provider", lambda current=None: None)

    changed: list[str] = []

    def _on_change_provider(provider: str):
        changed.append(provider)
        return ["new-model"], ""

    selected: list[str] = []

    def _on_select(model: str) -> None:
        selected.append(model)

    model_select.interactive_model_select(
        ["old-model"],
        "old-model",
        _on_select,
        current_provider="google",
        on_change_provider=_on_change_provider,
    )

    assert changed == []
    assert selected == []
