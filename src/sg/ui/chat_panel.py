"""Chat panel: a simple conversation form bound to a configured provider."""

from __future__ import annotations

import logging

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from sg import providers
from sg.db import Database, Provider
from sg.ui.model_field import ModelField
from sg.ui.workers import Worker, start_worker

logger = logging.getLogger(__name__)


class ChatPanel(QWidget):
    """Pick a chat provider, type a message and show the running conversation."""

    def __init__(self, parent=None, db: Database | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("chatPanel")
        self._db = db if db is not None else Database()
        self._messages: list[dict] = []
        self._thread: Worker | None = None

        self._provider_combo = QComboBox(self)
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)

        self._model_edit = ModelField(self)
        self._model_edit.setPlaceholderText("Model")

        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Kết nối", self))
        header_row.addWidget(self._provider_combo, 1)
        header_row.addWidget(QLabel("Model", self))
        header_row.addWidget(self._model_edit, 1)

        self._transcript = QTextBrowser(self)
        self._transcript.setObjectName("chatTranscript")
        self._transcript.setOpenExternalLinks(True)

        self._input = QPlainTextEdit(self)
        self._input.setPlaceholderText("Nhập tin nhắn… (Ctrl+Enter để gửi)")
        self._input.setFixedHeight(80)
        self._input.installEventFilter(self)

        self._send_button = QPushButton("Gửi", self)
        self._send_button.setProperty("variant", "primary")
        self._send_button.clicked.connect(self.send)

        self._status = QLabel(self)
        self._status.setObjectName("subtitle")

        input_row = QHBoxLayout()
        input_row.addWidget(self._input, 1)
        input_row.addWidget(self._send_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addLayout(header_row)
        layout.addWidget(self._transcript, 1)
        layout.addLayout(input_row)
        layout.addWidget(self._status)

        self.refresh()

    # --------------------------------------------------------------- state
    def refresh(self, select_id: int | None = None) -> None:
        """Reload the provider list, keeping the current selection when possible."""
        current = self._selected_id()
        if select_id is not None:
            current = select_id
        self._provider_combo.blockSignals(True)
        self._provider_combo.clear()
        for provider in self._db.list_providers():
            self._provider_combo.addItem(provider.name, provider.id)
        index = self._provider_combo.findData(current)
        if index >= 0:
            self._provider_combo.setCurrentIndex(index)
        self._provider_combo.blockSignals(False)
        self._on_provider_changed()
        self._update_send_state()

    def _selected_id(self) -> int | None:
        return self._provider_combo.currentData()

    def _current_provider(self) -> Provider | None:
        provider_id = self._selected_id()
        if provider_id is None:
            return None
        return self._db.get_provider(int(provider_id))

    def _on_provider_changed(self) -> None:
        provider = self._current_provider()
        if provider is None:
            self._model_edit.set_endpoint("", "", providers.DEFAULT_KIND)
            self._model_edit.clear()
            return
        self._model_edit.set_endpoint(provider.base_url, provider.api_key, provider.kind)
        if provider.default_model:
            self._model_edit.setText(provider.default_model)
        self._status.clear()

    # --------------------------------------------------------------- actions
    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (Qt override)
        if obj is self._input and event.type() == QEvent.Type.KeyPress:
            ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            if ctrl and enter:
                self.send()
                return True
        return super().eventFilter(obj, event)

    def send(self, text: str | None = None) -> None:
        """Send the input (or ``text``) to the selected provider."""
        if self._thread is not None:
            return
        message = (self._input.toPlainText() if text is None else text).strip()
        if not message:
            return
        provider = self._current_provider()
        if provider is None:
            self._status.setText("Chưa có kết nối AI nào. Thêm trong “Cài đặt AI”.")
            return
        model = self._model_edit.text().strip() or provider.default_model
        if not model:
            self._status.setText("Chưa chọn model cho kết nối này.")
            return

        self._input.clear()
        self._messages.append({"role": "user", "content": message})
        self._transcript.append(f"<b>Bạn:</b> {self._escape(message)}")
        self._status.setText("Đang trả lời…")
        self._send_button.setEnabled(False)

        base_url, api_key = provider.base_url, provider.api_key
        history = list(self._messages)
        self._thread = start_worker(
            lambda: providers.chat_completion(base_url, api_key, model, history),
            on_success=self._on_reply,
            on_error=self._on_error,
            on_finished=self._on_finished,
        )

    def _on_reply(self, reply: str) -> None:
        self._messages.append({"role": "assistant", "content": reply})
        self._transcript.append(f"<b>AI:</b> {self._escape(reply)}")
        self._status.clear()

    def _on_error(self, message: str) -> None:
        logger.error("Chat request failed: %s", message)
        self._status.setText(f"Lỗi: {message}")

    def _on_finished(self) -> None:
        self._thread = None
        self._update_send_state()

    # --------------------------------------------------------------- helpers
    def _update_send_state(self) -> None:
        self._send_button.setEnabled(self._provider_combo.count() > 0 and self._thread is None)

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
