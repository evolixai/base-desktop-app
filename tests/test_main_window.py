import pytest
from PySide6.QtWidgets import QMessageBox, QWidget
from pytestqt.qtbot import QtBot

from sg.db import Database
from sg.ui import workspace as workspace_module
from sg.ui.main_window import MainWindow
from sg.ui.project_dialog import ProjectDialog
from sg.ui.workspace import ProjectWorkspace


@pytest.fixture
def db() -> Database:
    return Database()


@pytest.fixture(autouse=True)
def _stub_browser(monkeypatch) -> None:
    """Avoid spinning up QtWebEngine in workspace tests."""
    monkeypatch.setattr(workspace_module, "BrowserTab", QWidget)


def test_window_title(qtbot: QtBot, db: Database) -> None:
    window = MainWindow(db)
    qtbot.addWidget(window)
    assert window.windowTitle() == "Sg"


def test_lists_existing_projects(qtbot: QtBot, db: Database) -> None:
    db.create_project("Alpha", "first")
    db.create_project("Beta", "second")

    window = MainWindow(db)
    qtbot.addWidget(window)

    assert window._table.rowCount() == 2
    names = {window._table.item(row, 0).text() for row in range(2)}
    assert names == {"Alpha", "Beta"}


def test_add_project(qtbot: QtBot, db: Database, monkeypatch) -> None:
    window = MainWindow(db)
    qtbot.addWidget(window)

    def fake_exec(self) -> int:
        self.name_edit.setText("New")
        self.description_edit.setPlainText("desc")
        return ProjectDialog.DialogCode.Accepted

    monkeypatch.setattr(ProjectDialog, "exec", fake_exec)
    window.add_project()

    assert window._table.rowCount() == 1
    assert window._table.item(0, 0).text() == "New"
    assert window._table.item(0, 1).text() == "desc"
    assert db.list_projects()[0].name == "New"


def test_edit_project(qtbot: QtBot, db: Database, monkeypatch) -> None:
    project = db.create_project("Alpha", "old")
    window = MainWindow(db)
    qtbot.addWidget(window)
    window._table.selectRow(0)

    def fake_exec(self) -> int:
        self.name_edit.setText("Renamed")
        self.description_edit.setPlainText("new")
        return ProjectDialog.DialogCode.Accepted

    monkeypatch.setattr(ProjectDialog, "exec", fake_exec)
    window._edit_selected()

    updated = db.get_project(project.id)
    assert updated is not None
    assert updated.name == "Renamed"
    assert updated.description == "new"
    assert window._table.item(0, 0).text() == "Renamed"
    assert window._table.item(0, 1).text() == "new"


def test_delete_project(qtbot: QtBot, db: Database, monkeypatch) -> None:
    project = db.create_project("Alpha")
    window = MainWindow(db)
    qtbot.addWidget(window)

    window._table.selectRow(0)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    window.delete_selected()

    assert window._table.rowCount() == 0
    assert db.get_project(project.id) is None


def test_opens_settings_dialog(qtbot: QtBot, db: Database, monkeypatch) -> None:
    window = MainWindow(db)
    qtbot.addWidget(window)

    opened: list[bool] = []
    monkeypatch.setattr("sg.ui.main_window.SettingsDialog.exec", lambda self: opened.append(True))
    window._settings_button.click()
    assert opened == [True]


def test_open_selected_shows_workspace(qtbot: QtBot, db: Database) -> None:
    db.create_project("Alpha")
    window = MainWindow(db)
    qtbot.addWidget(window)
    window._table.selectRow(0)

    window.open_selected()
    workspace = window._root_stack.currentWidget()
    assert isinstance(workspace, ProjectWorkspace)

    workspace.closed.emit()
    assert window._root_stack.currentIndex() == 0


def test_edit_button_enabled_only_with_selection(qtbot: QtBot, db: Database) -> None:
    db.create_project("Alpha")
    window = MainWindow(db)
    qtbot.addWidget(window)

    assert not window._edit_button.isEnabled()
    window._table.selectRow(0)
    assert window._edit_button.isEnabled()
