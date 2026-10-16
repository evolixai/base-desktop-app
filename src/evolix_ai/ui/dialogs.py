"""Localized message boxes.

Qt's standard buttons (OK/Cancel/Yes/No) are not covered by the app's own
catalogue, so the helpers here set their labels explicitly. They also keep the
call sites free of the QMessageBox boilerplate.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from evolix_ai.i18n import tr


def _localize(box: QMessageBox) -> None:
    for button, label in (
        (QMessageBox.StandardButton.Ok, tr("button.ok")),
        (QMessageBox.StandardButton.Yes, tr("button.yes")),
        (QMessageBox.StandardButton.No, tr("button.no")),
    ):
        widget = box.button(button)
        if widget is not None:
            widget.setText(label)


def confirm(parent, title: str, text: str) -> bool:
    """Ask a yes/no question; return True when the user confirms."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    box.setDefaultButton(QMessageBox.StandardButton.No)
    _localize(box)
    # exec() returns the clicked standard button as an int; map it back for a typed compare.
    return QMessageBox.StandardButton(box.exec()) == QMessageBox.StandardButton.Yes


def warning(parent, title: str, text: str) -> None:
    """Show a warning with a localized OK button."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    _localize(box)
    box.exec()
