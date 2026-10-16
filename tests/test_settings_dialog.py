import pytest
from PySide6.QtWidgets import QDialog
from pytestqt.qtbot import QtBot

from sg import providers
from sg.db import Database
from sg.ui.settings_dialog import ProviderDialog, SettingsDialog


@pytest.fixture
def db() -> Database:
    return Database()


def test_preset_kind_fills_and_locks_base_url(qtbot: QtBot) -> None:
    dialog = ProviderDialog()
    qtbot.addWidget(dialog)

    index = dialog.kind_combo.findData("zen")
    dialog.kind_combo.setCurrentIndex(index)

    assert dialog.base_url() == "https://opencode.ai/zen/v1"
    assert dialog.base_url_edit.isReadOnly()


def test_custom_kind_allows_editing_base_url(qtbot: QtBot) -> None:
    dialog = ProviderDialog()
    qtbot.addWidget(dialog)

    index = dialog.kind_combo.findData("custom")
    dialog.kind_combo.setCurrentIndex(index)
    dialog.base_url_edit.setText("https://localhost:1234/v1")

    assert not dialog.base_url_edit.isReadOnly()
    assert dialog.base_url() == "https://localhost:1234/v1"


def test_test_connection_reports_model_count(qtbot: QtBot, monkeypatch) -> None:
    dialog = ProviderDialog()
    qtbot.addWidget(dialog)
    dialog.kind_combo.setCurrentIndex(dialog.kind_combo.findData("zen"))

    monkeypatch.setattr(providers, "fetch_models", lambda url, key, **kw: ["a", "b", "c"])
    dialog._test_connection()
    qtbot.waitUntil(lambda: dialog._thread is None, timeout=2000)

    assert "3 model" in dialog._status.text()
    assert dialog._test_button.isEnabled()


def test_test_connection_reports_errors(qtbot: QtBot, monkeypatch) -> None:
    dialog = ProviderDialog()
    qtbot.addWidget(dialog)
    dialog.kind_combo.setCurrentIndex(dialog.kind_combo.findData("zen"))

    def boom(url: str, key: str, **kwargs: object) -> list[str]:
        raise providers.ProviderError("boom")

    monkeypatch.setattr(providers, "fetch_models", boom)
    dialog._test_connection()
    qtbot.waitUntil(lambda: dialog._thread is None, timeout=2000)

    assert dialog._status.text().startswith("Lỗi")


def test_model_field_autocompletes_from_endpoint(qtbot: QtBot, monkeypatch) -> None:
    dialog = ProviderDialog()
    qtbot.addWidget(dialog)
    dialog.kind_combo.setCurrentIndex(dialog.kind_combo.findData("custom"))
    dialog.base_url_edit.setText("https://x/v1")
    dialog.api_key_edit.setText("k")

    monkeypatch.setattr(providers, "fetch_models", lambda url, key, **kw: ["gpt-5.2", "gpt-5.3"])
    dialog.model_edit.refresh()

    qtbot.waitUntil(lambda: dialog.model_edit.suggestions() == ["gpt-5.2", "gpt-5.3"], timeout=2000)


def test_test_connection_seeds_model_suggestions(qtbot: QtBot, monkeypatch) -> None:
    dialog = ProviderDialog()
    qtbot.addWidget(dialog)
    dialog.kind_combo.setCurrentIndex(dialog.kind_combo.findData("zen"))

    monkeypatch.setattr(providers, "fetch_models", lambda url, key, **kw: ["a", "b", "c"])
    dialog._test_connection()
    qtbot.waitUntil(lambda: dialog._thread is None, timeout=2000)

    assert dialog.model_edit.suggestions() == ["a", "b", "c"]


def test_test_connection_ignores_second_click_while_running(qtbot: QtBot, monkeypatch) -> None:
    dialog = ProviderDialog()
    qtbot.addWidget(dialog)
    dialog.kind_combo.setCurrentIndex(dialog.kind_combo.findData("zen"))

    started: list[str] = []

    def slow(url: str, key: str, **kwargs: object) -> list[str]:
        started.append(url)
        return []

    monkeypatch.setattr(providers, "fetch_models", slow)
    dialog._test_connection()
    dialog._test_connection()  # must not start a second thread
    qtbot.waitUntil(lambda: dialog._thread is None, timeout=2000)

    assert started == ["https://opencode.ai/zen/v1"]


def test_cloudflare_kind_hints_editable_url(qtbot: QtBot) -> None:
    dialog = ProviderDialog()
    qtbot.addWidget(dialog)

    dialog.kind_combo.setCurrentIndex(dialog.kind_combo.findData("cloudflare"))

    assert not dialog.base_url_edit.isReadOnly()
    assert dialog.base_url_edit.placeholderText() == providers.CLOUDFLARE_URL_TEMPLATE


def test_switching_to_cloudflare_clears_preset_url(qtbot: QtBot) -> None:
    dialog = ProviderDialog()
    qtbot.addWidget(dialog)

    dialog.kind_combo.setCurrentIndex(dialog.kind_combo.findData("zen"))
    assert dialog.base_url() == "https://opencode.ai/zen/v1"

    dialog.kind_combo.setCurrentIndex(dialog.kind_combo.findData("cloudflare"))

    assert dialog.base_url() == ""


def test_add_provider_via_settings(qtbot: QtBot, db: Database, monkeypatch) -> None:
    dialog = SettingsDialog(db=db)
    qtbot.addWidget(dialog)

    def fake_exec(self) -> int:
        self.name_edit.setText("My Zen")
        self.kind_combo.setCurrentIndex(self.kind_combo.findData("zen"))
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(ProviderDialog, "exec", fake_exec)
    dialog._add()

    rows = db.list_providers()
    assert len(rows) == 1
    assert rows[0].name == "My Zen"
    assert rows[0].base_url == "https://opencode.ai/zen/v1"
    assert dialog._table.rowCount() == 1


def test_delete_provider_via_settings(qtbot: QtBot, db: Database, monkeypatch) -> None:
    from PySide6.QtWidgets import QMessageBox

    provider = db.create_provider("Zen", "zen", "https://opencode.ai/zen/v1")
    dialog = SettingsDialog(db=db)
    qtbot.addWidget(dialog)
    dialog._table.selectRow(0)

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    dialog._delete_selected()

    assert db.get_provider(provider.id) is None
    assert dialog._table.rowCount() == 0
