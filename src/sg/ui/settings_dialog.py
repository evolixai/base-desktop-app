"""Provider (AI connection) settings dialogs."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
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
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from sg import providers
from sg.db import Database, Provider
from sg.ui.model_field import ModelField
from sg.ui.workers import Worker, start_worker

_PRESET_URLS = frozenset(p.base_url for p in providers.PRESETS.values() if p.base_url)

logger = logging.getLogger(__name__)


class ProviderDialog(QDialog):
    """Collects a provider name, type, base URL, API key and default model."""

    def __init__(self, parent=None, provider: Provider | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sửa kết nối" if provider else "Thêm kết nối")
        self.setMinimumWidth(460)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("Ví dụ: OpenCode Zen")

        self.kind_combo = QComboBox(self)
        for kind in providers.KINDS:
            self.kind_combo.addItem(providers.label_for_kind(kind), kind)

        self.base_url_edit = QLineEdit(self)
        self.base_url_edit.setPlaceholderText("https://…/v1")

        self.api_key_edit = QLineEdit(self)
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("API key")

        self.model_edit = ModelField(self)
        self.model_edit.setPlaceholderText("Model mặc định (không bắt buộc)")

        form = QFormLayout()
        form.addRow("Tên", self.name_edit)
        form.addRow("Loại", self.kind_combo)
        form.addRow("Base URL", self.base_url_edit)
        form.addRow("API key", self.api_key_edit)
        form.addRow("Model", self.model_edit)

        self._status = QLabel(self)
        self._status.setObjectName("subtitle")
        self._test_button = QPushButton("Kiểm tra kết nối", self)
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
            self.name_edit.setText(providers.label_for_kind(self._current_kind()))

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
            providers.CLOUDFLARE_URL_TEMPLATE if kind == "cloudflare" else "https://…/v1"
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
            self._status.setText("Chưa có base URL để kiểm tra.")
            return

        self._status.setText("Đang kiểm tra…")
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
        self._status.setText(f"Kết nối OK · {len(models)} model{detail}")

    def _on_error(self, message: str) -> None:
        logger.error("Provider test failed: %s", message)
        self._status.setText(f"Lỗi: {message}")

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
            QMessageBox.warning(self, "Thiếu thông tin", "Tên kết nối không được để trống.")
            self.name_edit.setFocus()
            return
        if not self.base_url().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Base URL không được để trống.")
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

    def __init__(self, parent=None, db: Database | None = None) -> None:
        super().__init__(parent)
        self._db = db if db is not None else Database()
        self.setWindowTitle("Cài đặt kết nối AI")
        self.resize(680, 420)

        header = QLabel("Nhà cung cấp AI", self)
        header.setObjectName("title")
        hint = QLabel(
            "Kết nối dùng endpoint chat OpenAI-compatible. "
            "Cloudflare Workers AI nhập base URL dạng tài khoản.",
            self,
        )
        hint.setObjectName("subtitle")

        self._table = QTableWidget(0, 4, self)
        self._table.setHorizontalHeaderLabels(["Tên", "Loại", "Model", "Base URL"])
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

        self._add_button = QPushButton("Thêm", self)
        self._add_button.setProperty("variant", "primary")
        self._edit_button = QPushButton("Sửa", self)
        self._delete_button = QPushButton("Xoá", self)
        self._delete_button.setProperty("variant", "danger")
        self._add_button.clicked.connect(self._add)
        self._edit_button.clicked.connect(self._edit_selected)
        self._delete_button.clicked.connect(self._delete_selected)

        close_button = QPushButton("Đóng", self)
        close_button.clicked.connect(self.accept)

        actions = QHBoxLayout()
        actions.addWidget(self._add_button)
        actions.addWidget(self._edit_button)
        actions.addWidget(self._delete_button)
        actions.addStretch(1)
        actions.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(header)
        layout.addWidget(hint)
        layout.addWidget(self._table, 1)
        layout.addLayout(actions)

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
                QTableWidgetItem(providers.label_for_kind(provider.kind)),
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
        confirm = QMessageBox.question(
            self,
            "Xoá kết nối",
            f"Bạn có chắc muốn xoá “{provider.name}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._db.delete_provider(provider_id)
            self.refresh()
