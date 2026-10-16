"""Main application window: project list with CRUD actions."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sg.db import Database
from sg.ui.project_dialog import ProjectDialog
from sg.ui.settings_dialog import SettingsDialog
from sg.ui.workspace import ProjectWorkspace


class MainWindow(QMainWindow):
    def __init__(self, db: Database | None = None) -> None:
        super().__init__()
        self._db = db if db is not None else Database()

        self.setWindowTitle("Sg")
        self.resize(900, 600)

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self._root_stack = QStackedWidget(self)
        self._root_stack.setObjectName("central")
        self._root_stack.addWidget(self._build_projects_page())
        self.setCentralWidget(self._root_stack)

    def _build_projects_page(self) -> QWidget:
        central = QWidget()
        central.setObjectName("central")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Dự án", central)
        title.setObjectName("title")
        self._subtitle = QLabel(central)
        self._subtitle.setObjectName("subtitle")

        header = QVBoxLayout()
        header.setSpacing(2)
        header.addWidget(title)
        header.addWidget(self._subtitle)
        layout.addLayout(header)

        self._table = QTableWidget(0, 3, central)
        self._table.setHorizontalHeaderLabels(["Tên", "Mô tả", "Cập nhật"])
        for column in range(self._table.columnCount()):
            header_item = self._table.horizontalHeaderItem(column)
            if header_item is not None:
                header_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setDefaultSectionSize(38)
        self._table.doubleClicked.connect(self.open_selected)
        self._table.itemSelectionChanged.connect(self._update_actions)
        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self._empty = QLabel("Chưa có dự án nào.\nNhấn “Thêm dự án” để bắt đầu.", central)
        self._empty.setObjectName("emptyState")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._stack = QStackedWidget(central)
        self._stack.addWidget(self._table)
        self._stack.addWidget(self._empty)
        layout.addWidget(self._stack, 1)

        actions = QHBoxLayout()
        self._open_button = QPushButton("Mở", central)
        self._open_button.setProperty("variant", "primary")
        self._add_button = QPushButton("Thêm dự án", central)
        self._edit_button = QPushButton("Sửa", central)
        self._delete_button = QPushButton("Xoá", central)
        self._delete_button.setProperty("variant", "danger")
        self._open_button.clicked.connect(self.open_selected)
        self._add_button.clicked.connect(self.add_project)
        self._edit_button.clicked.connect(self._edit_selected)
        self._delete_button.clicked.connect(self.delete_selected)
        self._settings_button = QPushButton("Cài đặt AI", central)
        self._settings_button.clicked.connect(self.open_settings)
        actions.addWidget(self._open_button)
        actions.addWidget(self._add_button)
        actions.addWidget(self._edit_button)
        actions.addWidget(self._delete_button)
        actions.addStretch(1)
        actions.addWidget(self._settings_button)
        layout.addLayout(actions)

        return central

    # --------------------------------------------------------------- state
    def refresh(self, select_id: int | None = None) -> None:
        projects = self._db.list_projects()
        self._table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            name_item = QTableWidgetItem(project.name)
            name_item.setData(Qt.ItemDataRole.UserRole, project.id)
            description_item = QTableWidgetItem(project.description)
            updated_item = QTableWidgetItem(project.updated_at[:16])
            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, description_item)
            self._table.setItem(row, 2, updated_item)
            if select_id is not None and project.id == select_id:
                self._table.selectRow(row)

        self._subtitle.setText(f"{len(projects)} dự án")
        self._stack.setCurrentWidget(self._table if projects else self._empty)
        self._update_actions()

    def _selected_id(self) -> int | None:
        items = self._table.selectedItems()
        if not items:
            return None
        name_item = self._table.item(items[0].row(), 0)
        return name_item.data(Qt.ItemDataRole.UserRole) if name_item else None

    def _update_actions(self) -> None:
        has_selection = self._selected_id() is not None
        self._open_button.setEnabled(has_selection)
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self, db=self._db)
        dialog.exec()

    # ----------------------------------------------------------- workspace
    def open_selected(self) -> None:
        project_id = self._selected_id()
        if project_id is None:
            return
        project = self._db.get_project(project_id)
        if project is None:
            self.refresh()
            return
        workspace = ProjectWorkspace(project, self._db)
        workspace.closed.connect(self._show_projects)
        self._root_stack.addWidget(workspace)
        self._root_stack.setCurrentWidget(workspace)

    def _show_projects(self) -> None:
        workspace = self._root_stack.currentWidget()
        self._root_stack.setCurrentIndex(0)
        if isinstance(workspace, ProjectWorkspace):
            self._root_stack.removeWidget(workspace)
            workspace.deleteLater()

    # ------------------------------------------------------------- actions
    def add_project(self) -> None:
        dialog = ProjectDialog(self)
        if dialog.exec() == ProjectDialog.DialogCode.Accepted:
            project = self._db.create_project(dialog.name(), dialog.description())
            self.refresh(select_id=project.id)

    def _edit_selected(self) -> None:
        project_id = self._selected_id()
        if project_id is None:
            return
        project = self._db.get_project(project_id)
        if project is None:
            self.refresh()
            return
        dialog = ProjectDialog(self, project=project)
        if dialog.exec() == ProjectDialog.DialogCode.Accepted:
            self._db.update_project(project_id, dialog.name(), dialog.description())
            self.refresh(select_id=project_id)

    def delete_selected(self) -> None:
        project_id = self._selected_id()
        if project_id is None:
            return
        project = self._db.get_project(project_id)
        if project is None:
            self.refresh()
            return
        confirm = QMessageBox.question(
            self,
            "Xoá dự án",
            f"Bạn có chắc muốn xoá “{project.name}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._db.delete_project(project_id)
            self.refresh()
