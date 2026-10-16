from __future__ import annotations

import logging

from evolix_ai.ui.workers import Worker


def test_worker_logs_failure_with_traceback(caplog) -> None:
    def boom() -> None:
        raise ValueError("boom")

    worker = Worker(boom)

    with caplog.at_level(logging.ERROR, logger="evolix_ai.ui.workers"):
        worker.run()

    assert "Background worker" in caplog.text
    assert "boom" in caplog.text
    assert "Traceback" in caplog.text
