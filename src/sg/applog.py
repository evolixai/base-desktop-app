"""Application logging: daily log files, plus stderr when running from source.

The active file is ``sg.log``; each day's file is rolled over to
``sg-<YYYY-MM-DD>.log`` at midnight, keeping the most recent days.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from logging.handlers import BaseRotatingHandler, TimedRotatingFileHandler
from pathlib import Path
from types import TracebackType

APP_DATA_SUBDIR = Path(".evolix-ai") / "sg"
LOG_FILENAME = "sg.log"
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_ROTATED_SUFFIX = "%Y-%m-%d"
_KEEP_DAYS = 14

logger = logging.getLogger(__name__)


def log_dir() -> Path:
    """Return the app's log folder, creating it if missing."""
    directory = Path.home() / APP_DATA_SUBDIR / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def log_path() -> Path:
    return log_dir() / LOG_FILENAME


def _daily_namer(default_name: str) -> str:
    """Rename a rotated ``sg.log.<date>`` to ``sg-<date>.log``."""
    directory, base = os.path.split(default_name)
    prefix = f"{LOG_FILENAME}."
    if base.startswith(prefix):
        return os.path.join(directory, f"sg-{base[len(prefix) :]}.log")
    return default_name


def _install_excepthooks() -> None:
    """Route uncaught exceptions to the root logger instead of stderr only."""

    def handle(
        exc_type: type[BaseException], exc_value: BaseException, exc_tb: TracebackType | None
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    def handle_thread(args: threading.ExceptHookArgs) -> None:
        if issubclass(args.exc_type, KeyboardInterrupt):
            return
        name = args.thread.name if args.thread else "?"
        logger.critical(
            "Uncaught exception in thread %s",
            name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = handle
    threading.excepthook = handle_thread


def _install_qt_handler() -> None:
    """Forward Qt warnings/criticals to the logging system."""
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    except ImportError:
        return

    def handler(mode: QtMsgType, context: object, message: str) -> None:
        level = {
            QtMsgType.QtDebugMsg: logging.DEBUG,
            QtMsgType.QtInfoMsg: logging.INFO,
            QtMsgType.QtWarningMsg: logging.WARNING,
            QtMsgType.QtCriticalMsg: logging.ERROR,
            QtMsgType.QtFatalMsg: logging.CRITICAL,
        }.get(mode, logging.INFO)
        logger.log(level, "Qt: %s", message)

    qInstallMessageHandler(handler)


def setup_logging(*, level: int = logging.INFO) -> Path:
    """Configure root logging once and return the active log file path."""
    root = logging.getLogger()
    root.setLevel(level)
    _install_excepthooks()
    _install_qt_handler()
    if any(isinstance(handler, BaseRotatingHandler) for handler in root.handlers):
        return log_path()

    formatter = logging.Formatter(_FORMAT)
    file_handler = TimedRotatingFileHandler(
        log_path(), when="midnight", backupCount=_KEEP_DAYS, encoding="utf-8"
    )
    file_handler.suffix = _ROTATED_SUFFIX
    file_handler.namer = _daily_namer
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if not getattr(sys, "frozen", False):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    return log_path()
