"""Project workspace: the chat form plus an embedded browser."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from sg.db import Database, Project
from sg.ui.browser_tab import BrowserTab
from sg.ui.chat_panel import ChatPanel


class ProjectWorkspace(QWidget):
    """Hosts a project's chat form and browser, and signals when closed."""

    closed = Signal()

    def __init__(self, project: Project, db: Database, parent=None) -> None:
        super().__init__(parent)
        self._project = project
        self.setObjectName("central")

        back = QPushButton("← Projects", self)
        back.clicked.connect(self.closed.emit)

        title = QLabel(project.name, self)
        title.setObjectName("title")

        header = QHBoxLayout()
        header.addWidget(back)
        header.addWidget(title)
        header.addStretch(1)

        self.chat_panel = ChatPanel(self, db=db)
        tabs = QTabWidget(self)
        tabs.addTab(self.chat_panel, "Chat")
        tabs.addTab(BrowserTab(self), "Browser")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addLayout(header)
        layout.addWidget(tabs, 1)
