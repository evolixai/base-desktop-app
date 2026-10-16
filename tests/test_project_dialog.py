from pytestqt.qtbot import QtBot

from evolix_ai import i18n
from evolix_ai.db import Project
from evolix_ai.ui import project_dialog as project_dialog_module
from evolix_ai.ui.project_dialog import ProjectDialog


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
    monkeypatch.setattr(project_dialog_module, "warning", lambda *a, **k: None)

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


def test_dialog_follows_language(qtbot: QtBot) -> None:
    i18n.set_language("vi")
    dialog = ProjectDialog()
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Thêm dự án"
    assert dialog.description_edit.placeholderText() == "Mô tả ngắn (không bắt buộc)"
