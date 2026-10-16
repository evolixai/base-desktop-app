from __future__ import annotations

import threading
import time

from PySide6.QtCore import QEvent
from PySide6.QtGui import QFocusEvent
from pytestqt.qtbot import QtBot

from evolix_ai import providers
from evolix_ai.ui import workers
from evolix_ai.ui.model_field import ModelField


def test_focus_loads_models_for_endpoint(qtbot: QtBot, monkeypatch) -> None:
    monkeypatch.setattr(providers, "fetch_models", lambda base, key, **kw: ["a", "b"])
    field = ModelField()
    qtbot.addWidget(field)
    field.set_endpoint("https://x/v1", "k", "custom")

    field.focusInEvent(QFocusEvent(QEvent.Type.FocusIn))

    qtbot.waitUntil(lambda: field.suggestions() == ["a", "b"], timeout=2000)


def test_cached_models_return_when_endpoint_is_set_again(qtbot: QtBot, monkeypatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr(providers, "fetch_models", lambda *a, **k: calls.append(a) or ["a"])
    field = ModelField()
    qtbot.addWidget(field)
    field.set_endpoint("https://x/v1", "k", "custom")
    field.refresh()
    qtbot.waitUntil(lambda: field.suggestions() == ["a"], timeout=2000)

    field.set_endpoint("", "", "custom")
    assert field.suggestions() == []

    field.set_endpoint("https://x/v1", "k", "custom")
    assert field.suggestions() == ["a"]
    assert len(calls) == 1


def test_refresh_without_endpoint_does_not_fetch(qtbot: QtBot, monkeypatch) -> None:
    def _boom(*args, **kwargs):
        raise AssertionError("must not hit the network without an endpoint")

    monkeypatch.setattr(providers, "fetch_models", _boom)
    field = ModelField()
    qtbot.addWidget(field)

    field.refresh()

    assert field.suggestions() == []


def test_failed_fetch_is_cached_as_empty(qtbot: QtBot, monkeypatch) -> None:
    calls: list[object] = []

    def _boom(*args, **kwargs):
        calls.append(args)
        raise providers.ProviderError("boom")

    monkeypatch.setattr(providers, "fetch_models", _boom)
    field = ModelField()
    qtbot.addWidget(field)
    field.set_endpoint("https://x/v1", "k", "custom")

    field.refresh()
    qtbot.waitUntil(lambda: not workers._ACTIVE_WORKERS, timeout=2000)

    assert field.suggestions() == []
    # A failed lookup is cached, so a later refresh skips the dead endpoint.
    field.refresh()
    qtbot.wait(50)
    assert len(calls) == 1


def test_corrected_api_key_refetches_instead_of_reusing_failure(qtbot: QtBot, monkeypatch) -> None:
    keys: list[str] = []

    def fetch(base: str, key: str, **kwargs: object) -> list[str]:
        keys.append(key)
        if key == "bad":
            raise providers.ProviderError("boom")
        return ["a"]

    monkeypatch.setattr(providers, "fetch_models", fetch)
    field = ModelField()
    qtbot.addWidget(field)

    field.set_endpoint("https://x/v1", "bad", "custom")
    field.refresh()
    qtbot.waitUntil(lambda: not workers._ACTIVE_WORKERS, timeout=2000)
    assert field.suggestions() == []

    field.set_endpoint("https://x/v1", "good", "custom")
    field.refresh()

    qtbot.waitUntil(lambda: field.suggestions() == ["a"], timeout=2000)
    assert keys == ["bad", "good"]


def test_field_deleted_while_fetching_drops_result(qtbot: QtBot, monkeypatch) -> None:
    started = threading.Event()

    def slow(*args, **kwargs):
        started.set()
        time.sleep(0.3)
        return ["a"]

    monkeypatch.setattr(providers, "fetch_models", slow)
    field = ModelField()
    stored: list[object] = []
    field._store = lambda *args: stored.append(args)
    field.set_endpoint("https://x/v1", "k", "custom")
    field.refresh()
    assert started.wait(1.0)

    field.deleteLater()
    qtbot.waitUntil(lambda: not workers._ACTIVE_WORKERS, timeout=2000)

    # The in-flight result must not be delivered to the destroyed field.
    assert stored == []
