"""Embedded web browser tab built on QtWebEngine."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def normalize_url(text: str) -> QUrl:
    """Turn user input into a URL, inferring a scheme (and handling about: pages)."""
    return QUrl.fromUserInput(text.strip())


class BrowserTab(QWidget):
    """A minimal web browser: navigation bar plus a QWebEngineView."""

    title_changed = Signal(str)

    def __init__(self, parent=None, url: str = "") -> None:
        super().__init__(parent)
        self._view = None

        self._back = QPushButton("◀", self)
        self._forward = QPushButton("▶", self)
        self._reload = QPushButton("⟳", self)
        for button in (self._back, self._forward, self._reload):
            button.setFixedWidth(36)
        self._back.clicked.connect(lambda: self._view and self._view.back())
        self._forward.clicked.connect(lambda: self._view and self._view.forward())
        self._reload.clicked.connect(lambda: self._view and self._view.reload())

        self._address = QLineEdit(self)
        self._address.setPlaceholderText("Enter an address and press Enter…")
        self._address.returnPressed.connect(self._on_address_entered)

        nav = QHBoxLayout()
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(6)
        nav.addWidget(self._back)
        nav.addWidget(self._forward)
        nav.addWidget(self._reload)
        nav.addWidget(self._address, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addLayout(nav)

        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            hint = QLabel(
                "The embedded browser requires the PySide6-WebEngine package.\n"
                "Install it with: uv sync (or pip install PySide6-WebEngine).",
                self,
            )
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint.setObjectName("emptyState")
            layout.addWidget(hint, 1)
            return

        self._view = QWebEngineView(self)
        self._view.urlChanged.connect(self._on_url_changed)
        self._view.titleChanged.connect(self.title_changed.emit)
        layout.addWidget(self._view, 1)
        if url:
            self.navigate(url)

    # ------------------------------------------------------------- actions
    def navigate(self, url: str) -> None:
        target = normalize_url(url)
        if self._view is not None and target.isValid():
            self._view.setUrl(target)

    def _on_address_entered(self) -> None:
        self.navigate(self._address.text())

    def _on_url_changed(self, url: QUrl) -> None:
        self._address.setText(url.toString())
