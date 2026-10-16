from __future__ import annotations

from PySide6.QtWidgets import QMessageBox
from pytestqt.qtbot import QtBot

from evolix_ai import i18n
from evolix_ai.ui import dialogs

_ALL = (
    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
)


def _box() -> QMessageBox:
    box = QMessageBox()
    box.setStandardButtons(_ALL)
    return box


def test_localize_uses_english_labels(qtbot: QtBot) -> None:
    i18n.set_language("en")
    box = _box()
    qtbot.addWidget(box)

    dialogs._localize(box)

    assert box.button(QMessageBox.StandardButton.Ok).text() == "OK"
    assert box.button(QMessageBox.StandardButton.Yes).text() == "Yes"
    assert box.button(QMessageBox.StandardButton.No).text() == "No"


def test_localize_uses_vietnamese_labels(qtbot: QtBot) -> None:
    i18n.set_language("vi")
    box = _box()
    qtbot.addWidget(box)

    dialogs._localize(box)

    assert box.button(QMessageBox.StandardButton.Ok).text() == "OK"
    assert box.button(QMessageBox.StandardButton.Yes).text() == "Có"
    assert box.button(QMessageBox.StandardButton.No).text() == "Không"


def test_localize_skips_absent_buttons(qtbot: QtBot) -> None:
    box = QMessageBox()
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    qtbot.addWidget(box)

    dialogs._localize(box)

    assert box.button(QMessageBox.StandardButton.Ok).text() == "OK"
    assert box.button(QMessageBox.StandardButton.Yes) is None
