"""Application-wide Qt Style Sheet (the Qt equivalent of a CSS framework)."""

LIGHT_QSS = """
* {
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog, QWidget#central, QStackedWidget {
    background: #f8fafc;
}

QLabel {
    color: #111827;
    background: transparent;
}

QLabel#title {
    font-size: 24px;
    font-weight: 700;
}

QLabel#subtitle {
    color: #6b7280;
    font-size: 13px;
}

QLabel#emptyState {
    color: #9ca3af;
    font-size: 15px;
}

/* Buttons ---------------------------------------------------------------- */
QPushButton {
    background: #ffffff;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background: #f9fafb;
}

QPushButton:pressed {
    background: #f3f4f6;
}

QPushButton:disabled {
    color: #9ca3af;
    background: #f9fafb;
    border-color: #e5e7eb;
}

QPushButton[variant="primary"] {
    background: #4f46e5;
    color: #ffffff;
    border: 1px solid #4f46e5;
}

QPushButton[variant="primary"]:hover {
    background: #4338ca;
    border-color: #4338ca;
}

QPushButton[variant="primary"]:pressed {
    background: #3730a3;
    border-color: #3730a3;
}

QPushButton[variant="danger"] {
    color: #b91c1c;
    border: 1px solid #fecaca;
    background: #ffffff;
}

QPushButton[variant="danger"]:hover {
    background: #fef2f2;
}

QPushButton[variant="danger"]:disabled {
    color: #d1d5db;
    border-color: #f1f5f9;
    background: #ffffff;
}

/* Table ------------------------------------------------------------------ */
QTableWidget, QTableView {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    gridline-color: transparent;
    alternate-background-color: #fafafa;
    selection-background-color: #eef2ff;
    selection-color: #1f2937;
    outline: 0;
}

QTableWidget::item, QTableView::item {
    padding: 8px 10px;
    border-bottom: 1px solid #f1f3f5;
}

QTableWidget::item:selected, QTableView::item:selected {
    background: #eef2ff;
    color: #1f2937;
}

QHeaderView::section {
    background: #f9fafb;
    color: #6b7280;
    padding: 9px 10px;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    font-weight: 600;
}

QHeaderView::section:first {
    border-top-left-radius: 10px;
}

QHeaderView::section:last {
    border-top-right-radius: 10px;
}

QTableCornerButton::section {
    background: #f9fafb;
    border: none;
}

/* Inputs ----------------------------------------------------------------- */
QLineEdit, QPlainTextEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 7px 10px;
    color: #111827;
    selection-background-color: #c7d2fe;
    selection-color: #1f2937;
}

QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #4f46e5;
}

QLineEdit:read-only {
    background: #f3f4f6;
    color: #6b7280;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    selection-background-color: #eef2ff;
    selection-color: #1f2937;
    outline: 0;
}

/* Chat panel ------------------------------------------------------------- */
QTextBrowser#chatTranscript {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 8px;
}

/* Tabs ------------------------------------------------------------------- */
QTabWidget::pane {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    top: -1px;
}

QTabBar::tab {
    background: transparent;
    color: #6b7280;
    padding: 8px 16px;
    margin-right: 3px;
    border: 1px solid transparent;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:hover {
    color: #111827;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #111827;
    border-color: #e5e7eb;
    border-bottom-color: #ffffff;
    font-weight: 600;
}

/* Menus ------------------------------------------------------------------ */
QMenu {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 16px;
    border-radius: 6px;
}

QMenu::item:selected {
    background: #eef2ff;
    color: #1f2937;
}

/* Scrollbars ------------------------------------------------------------- */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #d1d5db;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #9ca3af;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #d1d5db;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #9ca3af;
}

QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
    height: 0;
    width: 0;
}
"""


def stylesheet() -> str:
    """Return the QSS to apply at the QApplication level."""
    return LIGHT_QSS.strip()
