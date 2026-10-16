"""AI provider presets and a minimal OpenAI-compatible chat client."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SESSION_ID = str(uuid.uuid4())

# Transient request failures (timeouts, 429, 5xx) are retried with backoff.
REQUEST_ATTEMPTS = 3
REQUEST_RETRY_BASE = 1.0
_RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def _retry(fn: Callable[[], object]) -> object:
    """Run ``fn``, retrying transient provider failures with exponential backoff."""
    for attempt in range(REQUEST_ATTEMPTS):
        try:
            return fn()
        except ProviderError as exc:
            if not exc.retryable or attempt == REQUEST_ATTEMPTS - 1:
                raise
            delay = REQUEST_RETRY_BASE * (2**attempt)
            logger.warning(
                "retry %d/%d in %.1fs: %s", attempt + 1, REQUEST_ATTEMPTS - 1, delay, exc
            )
            _sleep(delay)
    raise ProviderError("Could not complete the request.")


@dataclass(frozen=True, slots=True)
class ProviderPreset:
    kind: str
    label: str
    base_url: str


PRESETS: dict[str, ProviderPreset] = {
    "zen": ProviderPreset("zen", "OpenCode Zen", "https://opencode.ai/zen/v1"),
    "go": ProviderPreset("go", "OpenCode Go", "https://opencode.ai/zen/go/v1"),
    "cloudflare": ProviderPreset("cloudflare", "Cloudflare Workers AI", ""),
    "custom": ProviderPreset("custom", "Custom", ""),
}

DEFAULT_KIND = "custom"
KINDS: tuple[str, ...] = tuple(PRESETS)

# Cloudflare's account id lives in the URL; the model id is appended per request.
CLOUDFLARE_URL_TEMPLATE = "https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/run"
CLOUDFLARE_RUN_SUFFIX = "/ai/run"


def preset(kind: str) -> ProviderPreset:
    """Return the preset for ``kind``, falling back to the custom preset."""
    return PRESETS.get(kind, PRESETS[DEFAULT_KIND])


def label_for_kind(kind: str) -> str:
    return preset(kind).label


class ProviderError(RuntimeError):
    """Raised when a provider endpoint cannot be reached or returns an error.

    ``retryable`` marks failures worth retrying (timeouts, connection drops,
    HTTP 429/5xx) versus permanent ones (bad request, auth, not found).
    """

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


def endpoint(base_url: str, path: str) -> str:
    """Join a base URL with an API path, rejecting an empty base."""
    base = (base_url or "").strip().rstrip("/")
    if not base:
        raise ProviderError("No base URL configured.")
    return f"{base}/{path.lstrip('/')}"


def _build_request(
    url: str, headers: dict[str, str], payload: dict | None
) -> urllib.request.Request:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    if data is not None:
        headers = {**headers, "Content-Type": "application/json"}
    return urllib.request.Request(url, data=data, headers=headers)


def _urlopen(request: urllib.request.Request, timeout: float) -> bytes:
    logger.debug("request %s %s", request.get_method(), request.full_url)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        logger.error("HTTP %s from %s: %s", exc.code, request.full_url, detail)
        raise ProviderError(
            f"HTTP {exc.code}: {detail or exc.reason}",
            retryable=exc.code in _RETRYABLE_STATUS,
        ) from exc
    except urllib.error.URLError as exc:
        logger.error("connection error to %s: %s", request.full_url, exc.reason)
        raise ProviderError(f"Cannot connect: {exc.reason}", retryable=True) from exc
    except TimeoutError as exc:
        logger.error("timeout calling %s: %s", request.full_url, exc)
        raise ProviderError(f"Request timed out: {exc}", retryable=True) from exc


def _request_json(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict | None = None,
    timeout: float,
) -> object:
    raw = _urlopen(_build_request(url, headers, payload), timeout)
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Invalid response: {exc}") from exc


def _auth_headers(api_key: str) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Sg/0.1 (+https://opencode.ai)",
        "x-opencode-session": SESSION_ID,
    }
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"
    return headers


def fetch_models(
    base_url: str,
    api_key: str,
    *,
    kind: str = DEFAULT_KIND,
    timeout: float = 15.0,
) -> list[str]:
    """Return model ids from a provider's listing endpoint.

    Most providers expose an OpenAI-compatible ``/models`` route. Cloudflare
    Workers AI has no such route, so its account-level model search endpoint is
    queried instead.
    """
    if kind == "cloudflare":
        return _fetch_cloudflare_models(base_url, api_key, timeout=timeout)

    payload = _request_json(
        endpoint(base_url, "models"),
        headers=_auth_headers(api_key),
        timeout=timeout,
    )
    models = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        raise ProviderError("Response is missing the model list.")

    result: list[str] = []
    for item in models:
        if isinstance(item, dict) and item.get("id"):
            result.append(str(item["id"]))
        elif isinstance(item, str):
            result.append(item)
    return result


def _cloudflare_models_url(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if base.endswith(CLOUDFLARE_RUN_SUFFIX):
        base = base[: -len(CLOUDFLARE_RUN_SUFFIX)]
    return endpoint(base, "ai/models/search")


def _fetch_cloudflare_models(base_url: str, api_key: str, *, timeout: float) -> list[str]:
    payload = _request_json(
        _cloudflare_models_url(base_url),
        headers=_auth_headers(api_key),
        timeout=timeout,
    )
    if not isinstance(payload, dict) or not payload.get("success", True):
        message = "Cloudflare reported an error."
        errors = payload.get("errors") if isinstance(payload, dict) else None
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            message = str(errors[0].get("message") or message)
        raise ProviderError(message)

    models = payload.get("result")
    if not isinstance(models, list):
        raise ProviderError("Response is missing the model list.")

    result: list[str] = []
    for item in models:
        if isinstance(item, dict):
            name = item.get("name") or item.get("id")
            if name:
                result.append(str(name))
        elif isinstance(item, str):
            result.append(item)
    return result


def _request_chat_message(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict],
    *,
    temperature: float | None = None,
    timeout: float = 120.0,
) -> dict:
    """Send a chat request and return the assistant message dict.

    A reply is accepted when it carries text; an empty reply is retried as a
    transient failure.
    """
    payload: dict = {"model": model, "messages": messages}
    if temperature is not None:
        payload["temperature"] = temperature

    def fetch() -> dict:
        response = _request_json(
            endpoint(base_url, "chat/completions"),
            headers=_auth_headers(api_key),
            payload=payload,
            timeout=timeout,
        )
        choices = response.get("choices") if isinstance(response, dict) else None
        if not isinstance(choices, list) or not choices:
            raise ProviderError("Response has no reply content.", retryable=True)
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            raise ProviderError("Response has no reply content.", retryable=True)
        if not message.get("content"):
            raise ProviderError("Response has no reply content.", retryable=True)
        return message

    return _retry(fetch)


def chat_completion(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict],
    timeout: float = 120.0,
    *,
    temperature: float | None = None,
) -> str:
    """Send a chat conversation and return the assistant's reply text."""
    message = _request_chat_message(
        base_url, api_key, model, messages, temperature=temperature, timeout=timeout
    )
    content = message.get("content")
    if not content:
        raise ProviderError("Response has no reply content.", retryable=True)
    return str(content)
