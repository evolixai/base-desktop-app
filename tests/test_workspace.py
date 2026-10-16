from __future__ import annotations

import pytest
from PySide6.QtWidgets import QPushButton, QTabWidget, QWidget
from pytestqt.qtbot import QtBot

from evolix_ai.db import Database
from evolix_ai.ui import workspace as workspace_module
from evolix_ai.ui.workspace import ProjectWorkspace


@pytest.fixture(autouse=True)
def _stub_browser(monkeypatch) -> None:
    """Avoid spinning up QtWebEngine in workspace tests."""
    monkeypatch.setattr(workspace_module, "BrowserTab", QWidget)


def _workspace() -> ProjectWorkspace:
    db = Database()
    project = db.create_project("Alpha", "demo")
    return ProjectWorkspace(db.get_project(project.id), db)


def test_workspace_has_chat_and_browser_tabs(qtbot: QtBot) -> None:
    workspace = _workspace()
    qtbot.addWidget(workspace)

    tabs = workspace.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 2
    assert tabs.tabText(0) == "Chat"


def test_back_button_emits_closed(qtbot: QtBot) -> None:
    workspace = _workspace()
    qtbot.addWidget(workspace)

    fired: list[bool] = []
    workspace.closed.connect(lambda: fired.append(True))

    back = next(b for b in workspace.findChildren(QPushButton) if b.text() == "← Projects")
    back.click()

    assert fired == [True]
