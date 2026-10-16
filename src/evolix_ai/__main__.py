import sys
from pathlib import Path

from evolix_ai.applog import APP_DATA_SUBDIR, setup_logging


def _default_db_path() -> Path:
    from PySide6.QtCore import QStandardPaths

    root = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation)
    directory = Path(root or ".") / APP_DATA_SUBDIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "database.sqlite3"


def _run_gui() -> int:
    from PySide6.QtCore import QLocale, Qt
    from PySide6.QtWidgets import QApplication

    from evolix_ai import i18n
    from evolix_ai.db import Database
    from evolix_ai.ui import theme
    from evolix_ai.ui.main_window import MainWindow
    from evolix_ai.ui.workers import wait_for_active_workers

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("Evolix AI")
    app.setOrganizationName("Evolix AI")
    app.setStyle("Fusion")
    app.setStyleSheet(theme.stylesheet())

    db = Database(_default_db_path())
    app.aboutToQuit.connect(db.close)
    app.aboutToQuit.connect(wait_for_active_workers)

    saved_language = db.get_setting(i18n.SETTING_KEY)
    i18n.set_language(saved_language or i18n.normalize_language(QLocale.system().name()))

    window = MainWindow(db)
    window.showMaximized()

    return app.exec()


def main() -> int:
    setup_logging()
    return _run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
