from __future__ import annotations

import logging
import os
import sys
import threading

from evolix_ai import applog


def test_daily_namer_renames_rotated_file() -> None:
    assert applog._daily_namer(os.path.join("logs", "evolix-ai.log.2026-10-14")) == os.path.join(
        "logs", "evolix-ai-2026-10-14.log"
    )
    assert applog._daily_namer("other.txt") == "other.txt"


def test_setup_logging_writes_to_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(applog, "log_dir", lambda: tmp_path)
    root = logging.getLogger()
    original = list(root.handlers)
    for handler in original:
        root.removeHandler(handler)
    try:
        path = applog.setup_logging()

        logging.getLogger("evolix_ai.test").error("boom")

        for handler in root.handlers:
            handler.flush()
        assert path == tmp_path / "evolix-ai.log"
        assert "boom" in path.read_text(encoding="utf-8")
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
            handler.close()
        for handler in original:
            root.addHandler(handler)


def test_excepthook_routes_uncaught_exceptions_to_logger(monkeypatch, caplog) -> None:
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    monkeypatch.setattr(threading, "excepthook", threading.excepthook)
    applog._install_excepthooks()

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        exc_type, exc_value, exc_tb = sys.exc_info()

    with caplog.at_level(logging.CRITICAL, logger="evolix_ai.applog"):
        sys.excepthook(exc_type, exc_value, exc_tb)

    assert "Uncaught exception" in caplog.text
    assert "boom" in caplog.text
