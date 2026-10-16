from __future__ import annotations

import logging

from sg.ui.workers import Worker


def test_worker_logs_failure_with_traceback(caplog) -> None:
    def boom() -> None:
        raise ValueError("nổ")

    worker = Worker(boom)

    with caplog.at_level(logging.ERROR, logger="sg.ui.workers"):
        worker.run()

    assert "Background worker" in caplog.text
    assert "nổ" in caplog.text
    assert "Traceback" in caplog.text
