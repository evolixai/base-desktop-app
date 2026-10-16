from __future__ import annotations

from pytestqt.qtbot import QtBot

from evolix_ai import providers
from evolix_ai.db import Database
from evolix_ai.ui.chat_panel import ChatPanel


def _panel(db: Database) -> ChatPanel:
    return ChatPanel(db=db)


def test_provider_combo_lists_providers(qtbot: QtBot) -> None:
    db = Database()
    db.create_provider("Zen", "zen", "https://opencode.ai/zen/v1", "k", "gpt-5.2")
    panel = _panel(db)
    qtbot.addWidget(panel)

    assert panel._provider_combo.count() == 1
    assert panel._provider_combo.itemText(0) == "Zen"
    assert panel._model_edit.text() == "gpt-5.2"
    assert panel._send_button.isEnabled()


def test_send_without_provider_warns(qtbot: QtBot) -> None:
    panel = _panel(Database())
    qtbot.addWidget(panel)

    assert not panel._send_button.isEnabled()
    panel.send("hi")
    assert "No AI connection" in panel._status.text()


def test_send_appends_reply(qtbot: QtBot, monkeypatch) -> None:
    db = Database()
    db.create_provider("Zen", "zen", "https://opencode.ai/zen/v1", "k", "gpt-5.2")
    panel = _panel(db)
    qtbot.addWidget(panel)

    monkeypatch.setattr(providers, "chat_completion", lambda *a, **k: "Hello!")

    panel._input.setPlainText("Hi")
    panel.send()
    qtbot.waitUntil(lambda: panel._thread is None, timeout=2000)

    text = panel._transcript.toPlainText()
    assert "You: Hi" in text
    assert "AI: Hello!" in text
    assert panel._messages == [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]
    assert panel._input.toPlainText() == ""


def test_send_passes_provider_endpoint_and_history(qtbot: QtBot, monkeypatch) -> None:
    db = Database()
    db.create_provider("Zen", "zen", "https://opencode.ai/zen/v1", "secret", "gpt-5.2")
    panel = _panel(db)
    qtbot.addWidget(panel)

    captured: dict[str, object] = {}

    def fake(base_url, api_key, model, messages, *, session_id=None):
        captured["args"] = (base_url, api_key, model, messages)
        captured["session_id"] = session_id
        return "ok"

    monkeypatch.setattr(providers, "chat_completion", fake)

    panel.send("hello")
    qtbot.waitUntil(lambda: panel._thread is None, timeout=2000)

    assert captured["args"] == (
        "https://opencode.ai/zen/v1",
        "secret",
        "gpt-5.2",
        [{"role": "user", "content": "hello"}],
    )
    assert captured["session_id"] == panel._session_id


def test_send_reports_error(qtbot: QtBot, monkeypatch) -> None:
    db = Database()
    db.create_provider("Zen", "zen", "https://opencode.ai/zen/v1", "k", "gpt-5.2")
    panel = _panel(db)
    qtbot.addWidget(panel)

    def boom(*a, **k):
        raise providers.ProviderError("boom")

    monkeypatch.setattr(providers, "chat_completion", boom)

    panel.send("hi")
    qtbot.waitUntil(lambda: panel._thread is None, timeout=2000)

    assert panel._status.text().startswith("Error")


def test_send_button_click_sends(qtbot: QtBot, monkeypatch) -> None:
    db = Database()
    db.create_provider("Zen", "zen", "https://opencode.ai/zen/v1", "k", "gpt-5.2")
    panel = _panel(db)
    qtbot.addWidget(panel)

    monkeypatch.setattr(providers, "chat_completion", lambda *a, **k: "ok")

    panel._input.setPlainText("Hi")
    panel._send_button.click()
    qtbot.waitUntil(lambda: panel._thread is None, timeout=2000)

    assert "AI: ok" in panel._transcript.toPlainText()


def test_switching_provider_resets_model(qtbot: QtBot) -> None:
    db = Database()
    first = db.create_provider("A", "zen", "https://opencode.ai/zen/v1", "k", "gpt-5.2")
    second = db.create_provider("B", "zen", "https://opencode.ai/zen/v1", "k", "")
    panel = _panel(db)
    qtbot.addWidget(panel)

    assert panel._model_edit.text() == "gpt-5.2"

    panel._provider_combo.setCurrentIndex(panel._provider_combo.findData(second.id))
    assert panel._model_edit.text() == ""

    panel._provider_combo.setCurrentIndex(panel._provider_combo.findData(first.id))
    assert panel._model_edit.text() == "gpt-5.2"


def test_escape_html() -> None:
    assert ChatPanel._escape("<b>&\n</b>") == "&lt;b&gt;&amp;<br>&lt;/b&gt;"
