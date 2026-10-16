"""A model-id line edit that autocompletes a provider's available models."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QStringListModel, Qt
from PySide6.QtWidgets import QCompleter, QLineEdit

from sg import providers
from sg.ui.workers import start_worker

logger = logging.getLogger(__name__)

_Endpoint = tuple[str, str, str]


class _ModelFetch(QObject):
    """One provider-model lookup, owning the endpoint it was started for.

    It is parented to the field and connected through its bound methods, so a
    field destroyed mid-request drops these slots instead of firing them
    against a deleted widget.
    """

    def __init__(self, field: ModelField, endpoint: _Endpoint) -> None:
        super().__init__(field)
        self._field = field
        self._endpoint = endpoint

    def run(self) -> list[str]:
        base_url, api_key, kind = self._endpoint
        return providers.fetch_models(base_url, api_key, kind=kind)

    def store(self, models: list[str]) -> None:
        self._field._store(self._endpoint, models)

    def fail(self, message: str) -> None:
        self._field._fail(self._endpoint, message)

    def finish(self) -> None:
        self._field._finish(self._endpoint)


class ModelField(QLineEdit):
    """Line edit for a model id, with best-effort provider autocomplete.

    The endpoint's model ids are fetched off the GUI thread the first time the
    field gains focus and cached per endpoint (base URL, API key and kind). A
    failed lookup stores an empty list rather than surfacing an error:
    autocomplete is a convenience, and a real request reports problems properly.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._models: dict[_Endpoint, list[str]] = {}
        self._pending: dict[_Endpoint, _ModelFetch] = {}
        self._endpoint: _Endpoint | None = None

        self._completer = QCompleter(self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setModel(QStringListModel([], self))
        self.setCompleter(self._completer)

    # -------------------------------------------------------------- endpoint
    def set_endpoint(self, base_url: str, api_key: str, kind: str) -> None:
        """Target a provider endpoint and show whatever is cached for it."""
        self._endpoint = (base_url.strip(), api_key, kind)
        self._apply()

    def clear_suggestions(self) -> None:
        """Forget every cached model list (e.g. after providers change)."""
        self._models.clear()
        self._apply()

    def set_models(self, models: list[str]) -> None:
        """Seed suggestions from models fetched elsewhere, e.g. a test button."""
        if self._endpoint is None:
            return
        self._models[self._endpoint] = list(models)
        self._apply()

    def refresh(self) -> None:
        """Fetch the current endpoint's model ids, unless already known."""
        endpoint = self._endpoint
        if endpoint is None or not endpoint[0]:
            return
        if endpoint in self._models or endpoint in self._pending:
            return
        fetch = _ModelFetch(self, endpoint)
        self._pending[endpoint] = fetch
        start_worker(
            fetch.run,
            on_success=fetch.store,
            on_error=fetch.fail,
            on_finished=fetch.finish,
        )

    def suggestions(self) -> list[str]:
        """The model ids the completer currently offers."""
        model = self._completer.model()
        return model.stringList() if isinstance(model, QStringListModel) else []

    # ---------------------------------------------------------------- events
    def focusInEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().focusInEvent(event)
        self.refresh()

    # ----------------------------------------------------- worker callbacks
    def _store(self, endpoint: _Endpoint, models: list[str]) -> None:
        self._models[endpoint] = list(models)
        if self._endpoint == endpoint:
            self._apply()

    def _fail(self, endpoint: _Endpoint, message: str) -> None:
        # Cache the empty result so a dead endpoint is not retried on every
        # focus; a corrected API key yields a new endpoint and refetches.
        logger.info("Không tải được danh sách model cho %s: %s", endpoint[0], message)
        self._models[endpoint] = []

    def _finish(self, endpoint: _Endpoint) -> None:
        self._pending.pop(endpoint, None)

    # --------------------------------------------------------------- helpers
    def _apply(self) -> None:
        models = self._models.get(self._endpoint, []) if self._endpoint else []
        model = self._completer.model()
        if isinstance(model, QStringListModel):
            model.setStringList(models)
