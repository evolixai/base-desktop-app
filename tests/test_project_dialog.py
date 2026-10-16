from PySide6.QtWidgets import QMessageBox
from pytestqt.qtbot import QtBot

from sg.db import Project
from sg.ui.project_dialog import ProjectDialog


def test_name_and_description_are_trimmed(qtbot: QtBot) -> None:
    dialog = ProjectDialog()
    qtbot.addWidget(dialog)

    dialog.name_edit.setText("  Alpha  ")
    dialog.description_edit.setPlainText("  desc  ")

    assert dialog.name() == "Alpha"
    assert dialog.description() == "desc"


def test_empty_name_is_rejected(qtbot: QtBot, monkeypatch) -> None:
    dialog = ProjectDialog()
    qtbot.addWidget(dialog)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)

    dialog._on_accept()

    assert dialog.result() != ProjectDialog.DialogCode.Accepted


def test_edit_dialog_prefills_fields(qtbot: QtBot) -> None:
    project = Project(
        id=1,
        name="Alpha",
        description="first",
        created_at="",
        updated_at="",
    )
    dialog = ProjectDialog(project=project)
    qtbot.addWidget(dialog)

    assert dialog.name() == "Alpha"
    assert dialog.description() == "first"
    assert dialog.windowTitle() == "Edit project"
