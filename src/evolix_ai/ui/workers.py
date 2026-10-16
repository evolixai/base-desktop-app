"""Helpers to run blocking work off the GUI thread."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QCoreApplication, QObject, QThread, Signal

logger = logging.getLogger(__name__)

_ACTIVE_WORKERS: set[Worker] = set()


class Worker(QThread):
    """Runs a callable in a worker thread and reports its result via signals."""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[[], Any], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._fn = fn

    def run(self) -> None:
        try:
            result = self._fn()
        except Exception as exc:  # thread boundary: surface any failure to the UI
            logger.exception("Background worker %r failed", self._fn)
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(result)


def start_worker(
    fn: Callable[[], Any],
    *,
    on_success: Callable[[Any], None],
    on_error: Callable[[str], None],
    on_finished: Callable[[], None] | None = None,
) -> Worker:
    """Run ``fn`` off the GUI thread.

    The worker is owned by the application rather than the calling widget, so
    deleting that widget mid-request cannot destroy a running thread. It is also
    tracked until it finishes so it is never garbage-collected while running.

    Receivers are ordinary bound methods; PySide6 drops their connections
    automatically if the owning widget is destroyed, so results arriving after
    teardown are simply discarded.
    """
    worker = Worker(fn, QCoreApplication.instance())
    _ACTIVE_WORKERS.add(worker)
    worker.succeeded.connect(on_success)
    worker.failed.connect(on_error)
    if on_finished is not None:
        worker.finished.connect(on_finished)
    worker.finished.connect(lambda: _ACTIVE_WORKERS.discard(worker))
    worker.finished.connect(worker.deleteLater)
    worker.start()
    return worker


def wait_for_active_workers(timeout_ms: int = 3000) -> None:
    """Best-effort wait so in-flight workers are not destroyed while running."""
    for worker in list(_ACTIVE_WORKERS):
        worker.wait(timeout_ms)
