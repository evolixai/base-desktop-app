"""Add / edit project dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from evolix_ai.db import Project


class ProjectDialog(QDialog):
    """Collects a project's name and description."""

    def __init__(self, parent=None, project: Project | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit project" if project else "Add project")
        self.setMinimumWidth(420)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("Project name")
        self.description_edit = QPlainTextEdit(self)
        self.description_edit.setPlaceholderText("Short description (optional)")
        self.description_edit.setFixedHeight(110)

        form = QFormLayout()
        form.addRow("Name", self.name_edit)
        form.addRow("Description", self.description_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setProperty("variant", "primary")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if project is not None:
            self.name_edit.setText(project.name)
            self.description_edit.setPlainText(project.description)

        self.name_edit.setFocus()

    def _on_accept(self) -> None:
        if not self.name():
            QMessageBox.warning(self, "Missing information", "Project name is required.")
            self.name_edit.setFocus()
            return
        self.accept()

    def name(self) -> str:
        return self.name_edit.text().strip()

    def description(self) -> str:
        return self.description_edit.toPlainText().strip()
