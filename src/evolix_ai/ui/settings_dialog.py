"""Provider (AI connection) settings dialogs."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from evolix_ai import i18n, providers
from evolix_ai.db import Database, Provider
from evolix_ai.i18n import tr, trn
from evolix_ai.ui.dialogs import confirm, warning
from evolix_ai.ui.model_field import ModelField
from evolix_ai.ui.workers import Worker, start_worker

_PRESET_URLS = frozenset(p.base_url for p in providers.PRESETS.values() if p.base_url)

logger = logging.getLogger(__name__)


def _kind_label(kind: str) -> str:
    """Human label for a provider kind, with the generic one translated.

    Unknown kinds fall back to the custom preset, so they are translated too.
    """
    if providers.preset(kind).kind == providers.DEFAULT_KIND:
        return tr("provider.kind.custom")
    return providers.label_for_kind(kind)


class ProviderDialog(QDialog):
    """Collects a provider name, type, base URL, API key and default model."""

    def __init__(self, parent=None, provider: Provider | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("provider.edit_title") if provider else tr("provider.add_title"))
        self.setMinimumWidth(460)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText(tr("provider.name_placeholder"))

        self.kind_combo = QComboBox(self)
        for kind in providers.KINDS:
            self.kind_combo.addItem(_kind_label(kind), kind)

        self.base_url_edit = QLineEdit(self)
        self.base_url_edit.setPlaceholderText(tr("provider.base_url_placeholder"))

        self.api_key_edit = QLineEdit(self)
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText(tr("provider.api_key_placeholder"))

        self.model_edit = ModelField(self)
        self.model_edit.setPlaceholderText(tr("provider.model_placeholder"))

        form = QFormLayout()
        form.addRow(tr("field.name"), self.name_edit)
        form.addRow(tr("field.type"), self.kind_combo)
        form.addRow(tr("field.base_url"), self.base_url_edit)
        form.addRow(tr("field.api_key"), self.api_key_edit)
        form.addRow(tr("field.model"), self.model_edit)

        self._status = QLabel(self)
        self._status.setObjectName("subtitle")
        self._test_button = QPushButton(tr("provider.test_button"), self)
        self._test_button.clicked.connect(self._test_connection)

        test_row = QHBoxLayout()
        test_row.addWidget(self._test_button)
        test_row.addWidget(self._status, 1)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        ok_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setProperty("variant", "primary")
            ok_button.setText(tr("button.ok"))
        cancel_button = self._buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setText(tr("button.cancel"))
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        self._thread: Worker | None = None

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(test_row)
        layout.addWidget(self._buttons)

        self.kind_combo.currentIndexChanged.connect(self._on_kind_changed)
        self.base_url_edit.textChanged.connect(self._sync_model_endpoint)
        self.api_key_edit.textChanged.connect(self._sync_model_endpoint)

        if provider is not None:
            self.name_edit.setText(provider.name)
            index = self.kind_combo.findData(provider.kind)
            if index >= 0:
                self.kind_combo.setCurrentIndex(index)
            self.base_url_edit.setText(provider.base_url)
            self.api_key_edit.setText(provider.api_key)
            self.model_edit.setText(provider.default_model)
        else:
            self.name_edit.setText(_kind_label(self._current_kind()))

        self._on_kind_changed()
        self.name_edit.setFocus()

    # -------------------------------------------------------------- helpers
    def _current_kind(self) -> str:
        return self.kind_combo.currentData() or providers.DEFAULT_KIND

    def _on_kind_changed(self) -> None:
        kind = self._current_kind()
        editable = kind in (providers.DEFAULT_KIND, "cloudflare")
        if not editable:
            self.base_url_edit.setText(providers.preset(kind).base_url)
        elif self.base_url_edit.text().strip() in _PRESET_URLS:
            self.base_url_edit.clear()
        self.base_url_edit.setReadOnly(not editable)
        self.base_url_edit.setPlaceholderText(
            providers.CLOUDFLARE_URL_TEMPLATE
            if kind == "cloudflare"
            else tr("provider.base_url_placeholder")
        )
        self._sync_model_endpoint()
        self._status.clear()

    def _sync_model_endpoint(self) -> None:
        self.model_edit.set_endpoint(self.base_url(), self.api_key(), self._current_kind())

    def _test_connection(self) -> None:
        if self._thread is not None:
            return
        base_url = self.base_url()
        if not base_url:
            self._status.setText(tr("provider.no_base_url"))
            return

        self._status.setText(tr("provider.testing"))
        self._test_button.setEnabled(False)
        self._buttons.setEnabled(False)

        api_key = self.api_key()
        kind = self._current_kind()
        self.model_edit.set_endpoint(base_url, api_key, kind)
        self._thread = start_worker(
            lambda: providers.fetch_models(base_url, api_key, kind=kind),
            on_success=self._on_models,
            on_error=self._on_error,
            on_finished=self._on_test_finished,
        )

    def _on_models(self, models: list[str]) -> None:
        self.model_edit.set_models(models)
        preview = ", ".join(models[:3])
        if len(models) > 3:
            preview = f"{preview}…"
        detail = f": {preview}" if preview else ""
        label = trn("provider.model", len(models))
        self._status.setText(tr("provider.ok", count=len(models), label=label, detail=detail))

    def _on_error(self, message: str) -> None:
        logger.error("Provider test failed: %s", message)
        self._status.setText(tr("common.error", message=message))

    def _on_test_finished(self) -> None:
        self._test_button.setEnabled(True)
        self._buttons.setEnabled(True)
        self._thread = None

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._thread is not None:
            event.ignore()
            return
        super().closeEvent(event)

    def _on_accept(self) -> None:
        if not self.name().strip():
            warning(self, tr("dialog.missing_info"), tr("provider.name_required"))
            self.name_edit.setFocus()
            return
        if not self.base_url().strip():
            warning(self, tr("dialog.missing_info"), tr("provider.base_url_required"))
            self.base_url_edit.setFocus()
            return
        self.accept()

    # --------------------------------------------------------------- values
    def name(self) -> str:
        return self.name_edit.text().strip()

    def kind(self) -> str:
        return self._current_kind()

    def base_url(self) -> str:
        return self.base_url_edit.text().strip()

    def api_key(self) -> str:
        return self.api_key_edit.text().strip()

    def model(self) -> str:
        return self.model_edit.text().strip()


class SettingsDialog(QDialog):
    """Lists configured AI providers and lets the user manage them."""

    language_changed = Signal(str)

    def __init__(self, parent=None, db: Database | None = None) -> None:
        super().__init__(parent)
        self._db = db if db is not None else Database()
        self.setWindowTitle(tr("settings.title"))
        self.resize(680, 420)

        self._header = QLabel(tr("settings.header"), self)
        self._header.setObjectName("title")
        self._hint = QLabel(tr("settings.hint"), self)
        self._hint.setObjectName("subtitle")

        self._language_label = QLabel(tr("settings.language"), self)
        self._language_combo = QComboBox(self)
        for code, label in i18n.available_languages():
            self._language_combo.addItem(label, code)
        index = self._language_combo.findData(i18n.current_language())
        if index >= 0:
            self._language_combo.setCurrentIndex(index)
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)

        language_row = QHBoxLayout()
        language_row.addWidget(self._language_label)
        language_row.addWidget(self._language_combo)
        language_row.addStretch(1)

        self._table = QTableWidget(0, 4, self)
        self._table.setHorizontalHeaderLabels(self._column_labels())
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setDefaultSectionSize(38)
        self._table.doubleClicked.connect(self._edit_selected)
        self._table.itemSelectionChanged.connect(self._update_actions)
        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self._add_button = QPushButton(tr("action.add"), self)
        self._add_button.setProperty("variant", "primary")
        self._edit_button = QPushButton(tr("action.edit"), self)
        self._delete_button = QPushButton(tr("action.delete"), self)
        self._delete_button.setProperty("variant", "danger")
        self._add_button.clicked.connect(self._add)
        self._edit_button.clicked.connect(self._edit_selected)
        self._delete_button.clicked.connect(self._delete_selected)

        self._close_button = QPushButton(tr("action.close"), self)
        self._close_button.clicked.connect(self.accept)

        actions = QHBoxLayout()
        actions.addWidget(self._add_button)
        actions.addWidget(self._edit_button)
        actions.addWidget(self._delete_button)
        actions.addStretch(1)
        actions.addWidget(self._close_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(self._header)
        layout.addWidget(self._hint)
        layout.addLayout(language_row)
        layout.addWidget(self._table, 1)
        layout.addLayout(actions)

        self.refresh()

    @staticmethod
    def _column_labels() -> list[str]:
        return [tr("field.name"), tr("field.type"), tr("field.model"), tr("field.base_url")]

    def _on_language_changed(self) -> None:
        code = self._language_combo.currentData()
        if not code or code == i18n.current_language():
            return
        i18n.set_language(code)
        self._db.set_setting(i18n.SETTING_KEY, code)
        self._retranslate()
        self.language_changed.emit(code)

    def _retranslate(self) -> None:
        """Re-apply the dialog's own texts after a language change."""
        self.setWindowTitle(tr("settings.title"))
        self._header.setText(tr("settings.header"))
        self._hint.setText(tr("settings.hint"))
        self._language_label.setText(tr("settings.language"))
        self._table.setHorizontalHeaderLabels(self._column_labels())
        self._add_button.setText(tr("action.add"))
        self._edit_button.setText(tr("action.edit"))
        self._delete_button.setText(tr("action.delete"))
        self._close_button.setText(tr("action.close"))
        self.refresh()

    # --------------------------------------------------------------- state
    def refresh(self, select_id: int | None = None) -> None:
        rows = self._db.list_providers()
        self._table.setRowCount(len(rows))
        for row, provider in enumerate(rows):
            name_item = QTableWidgetItem(provider.name)
            name_item.setData(Qt.ItemDataRole.UserRole, provider.id)
            cells = [
                name_item,
                QTableWidgetItem(_kind_label(provider.kind)),
                QTableWidgetItem(provider.default_model),
                QTableWidgetItem(provider.base_url),
            ]
            for column, item in enumerate(cells):
                self._table.setItem(row, column, item)
            if select_id is not None and provider.id == select_id:
                self._table.selectRow(row)
        self._update_actions()

    def _selected_id(self) -> int | None:
        items = self._table.selectedItems()
        if not items:
            return None
        name_item = self._table.item(items[0].row(), 0)
        return name_item.data(Qt.ItemDataRole.UserRole) if name_item else None

    def _update_actions(self) -> None:
        has_selection = self._selected_id() is not None
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    # ------------------------------------------------------------- actions
    def _add(self) -> None:
        dialog = ProviderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            provider = self._db.create_provider(
                dialog.name(),
                dialog.kind(),
                dialog.base_url(),
                dialog.api_key(),
                dialog.model(),
            )
            self.refresh(select_id=provider.id)

    def _edit_selected(self) -> None:
        provider_id = self._selected_id()
        if provider_id is None:
            return
        provider = self._db.get_provider(provider_id)
        if provider is None:
            self.refresh()
            return
        dialog = ProviderDialog(self, provider=provider)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._db.update_provider(
                provider_id,
                dialog.name(),
                dialog.kind(),
                dialog.base_url(),
                dialog.api_key(),
                dialog.model(),
            )
            self.refresh(select_id=provider_id)

    def _delete_selected(self) -> None:
        provider_id = self._selected_id()
        if provider_id is None:
            return
        provider = self._db.get_provider(provider_id)
        if provider is None:
            self.refresh()
            return
        if confirm(
            self,
            tr("provider.delete.title"),
            tr("provider.delete.text", name=provider.name),
        ):
            self._db.delete_provider(provider_id)
            self.refresh()
