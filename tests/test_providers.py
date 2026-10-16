import io
import json
import urllib.error

import pytest

from evolix_ai import providers


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def test_fetch_models_parses_openai_payload(monkeypatch) -> None:
    body = json.dumps({"data": [{"id": "a"}, {"id": "b"}, "c", {"nope": 1}]}).encode()
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["accept"] = request.get_header("Accept")
        return _FakeResponse(body)

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)

    assert providers.fetch_models("https://opencode.ai/zen/v1/", "sk-1") == ["a", "b", "c"]
    assert captured["url"] == "https://opencode.ai/zen/v1/models"
    assert captured["auth"] == "Bearer sk-1"
    assert captured["accept"] == "application/json"


def test_fetch_models_omits_auth_header_without_key(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=None):
        captured["auth"] = request.get_header("Authorization")
        return _FakeResponse(b'{"data": []}')

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    assert providers.fetch_models("https://x/v1", "  ") == []
    assert captured["auth"] is None


def test_fetch_models_rejects_empty_base_url() -> None:
    with pytest.raises(providers.ProviderError):
        providers.fetch_models("   ", "sk-1")


def test_fetch_models_reports_http_error(monkeypatch) -> None:
    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, io.BytesIO(b"bad"))

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(providers.ProviderError) as excinfo:
        providers.fetch_models("https://x/v1", "sk-1")
    assert "401" in str(excinfo.value)
    assert "bad" in str(excinfo.value)


def test_fetch_models_reports_connection_error(monkeypatch) -> None:
    def fake_urlopen(request, timeout=None):
        raise urllib.error.URLError("refused")

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(providers.ProviderError):
        providers.fetch_models("https://x/v1", "sk-1")


def test_fetch_models_rejects_invalid_json(monkeypatch) -> None:
    def fake_urlopen(request, timeout=None):
        return _FakeResponse(b"not json")

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(providers.ProviderError):
        providers.fetch_models("https://x/v1", "sk-1")


def test_fetch_models_rejects_missing_data(monkeypatch) -> None:
    def fake_urlopen(request, timeout=None):
        return _FakeResponse(b'{"object": "list"}')

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(providers.ProviderError):
        providers.fetch_models("https://x/v1", "sk-1")


def test_fetch_models_cloudflare_queries_model_search(monkeypatch) -> None:
    body = json.dumps(
        {"success": True, "result": [{"name": "@cf/m"}, "@cf/n", {"id": "@cf/o"}]}
    ).encode()
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        return _FakeResponse(body)

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)

    result = providers.fetch_models(
        "https://api.cloudflare.com/client/v4/accounts/acc/ai/run",
        "tok",
        kind="cloudflare",
    )

    assert result == ["@cf/m", "@cf/n", "@cf/o"]
    assert captured["url"] == ("https://api.cloudflare.com/client/v4/accounts/acc/ai/models/search")
    assert captured["auth"] == "Bearer tok"


def test_fetch_models_cloudflare_reports_api_error(monkeypatch) -> None:
    body = json.dumps(
        {"success": False, "errors": [{"code": 7000, "message": "No route"}]}
    ).encode()

    def fake_urlopen(request, timeout=None):
        return _FakeResponse(body)

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(providers.ProviderError) as excinfo:
        providers.fetch_models(
            "https://api.cloudflare.com/client/v4/accounts/acc/ai/run",
            "tok",
            kind="cloudflare",
        )
    assert "No route" in str(excinfo.value)


def test_fetch_models_cloudflare_rejects_empty_base_url() -> None:
    with pytest.raises(providers.ProviderError):
        providers.fetch_models("   ", "tok", kind="cloudflare")


def test_chat_completion_posts_messages_and_returns_text(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(b'{"choices":[{"message":{"content":"ok"}}]}')

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)

    reply = providers.chat_completion("https://x/v1", "k", "m", [{"role": "user", "content": "hi"}])

    assert reply == "ok"
    assert captured["url"] == "https://x/v1/chat/completions"
    assert captured["auth"] == "Bearer k"
    assert captured["body"] == {"model": "m", "messages": [{"role": "user", "content": "hi"}]}


def test_chat_completion_sends_opencode_session_for_opencode_host(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=None):
        captured["session"] = request.headers.get("X-opencode-session")
        return _FakeResponse(b'{"choices":[{"message":{"content":"ok"}}]}')

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)

    providers.chat_completion(
        "https://opencode.ai/zen/v1",
        "k",
        "m",
        [{"role": "user", "content": "hi"}],
        session_id="conv-1",
    )

    assert captured["session"] == "conv-1"


def test_chat_completion_omits_opencode_session_for_other_hosts(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=None):
        captured["session"] = request.headers.get("X-opencode-session")
        return _FakeResponse(b'{"choices":[{"message":{"content":"ok"}}]}')

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)

    providers.chat_completion(
        "https://api.example.com/v1",
        "k",
        "m",
        [{"role": "user", "content": "hi"}],
        session_id="conv-1",
    )

    assert captured["session"] is None


def test_fetch_models_omits_opencode_session(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=None):
        captured["session"] = request.headers.get("X-opencode-session")
        return _FakeResponse(b'{"data": []}')

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)

    providers.fetch_models("https://opencode.ai/zen/v1", "k")

    assert captured["session"] is None


def test_chat_completion_retries_transient_error(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_urlopen(request, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(request.full_url, 429, "Too Many", {}, io.BytesIO(b""))
        return _FakeResponse(b'{"choices":[{"message":{"content":"ok"}}]}')

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(providers, "_sleep", lambda _seconds: None)

    reply = providers.chat_completion("https://x/v1", "k", "m", [{"role": "user", "content": "hi"}])

    assert reply == "ok"
    assert calls["n"] == 2


def test_chat_completion_does_not_retry_client_error(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_urlopen(request, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, io.BytesIO(b"bad"))

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(providers, "_sleep", lambda _seconds: None)

    with pytest.raises(providers.ProviderError):
        providers.chat_completion("https://x/v1", "k", "m", [{"role": "user", "content": "hi"}])

    assert calls["n"] == 1


def test_chat_completion_retries_empty_content(monkeypatch) -> None:
    bodies = [b'{"choices":[]}', b'{"choices":[{"message":{"content":"ok"}}]}']
    sleeps: list[float] = []

    def fake_urlopen(request, timeout=None):
        return _FakeResponse(bodies.pop(0))

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(providers, "_sleep", sleeps.append)

    reply = providers.chat_completion("https://x/v1", "k", "m", [{"role": "user", "content": "hi"}])

    assert reply == "ok"
    assert sleeps == [providers.REQUEST_RETRY_BASE]


def test_chat_completion_gives_up_after_empty_replies(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_urlopen(request, timeout=None):
        calls["n"] += 1
        return _FakeResponse(b'{"choices":[]}')

    monkeypatch.setattr(providers.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(providers, "_sleep", lambda _seconds: None)

    with pytest.raises(providers.ProviderError):
        providers.chat_completion("https://x/v1", "k", "m", [{"role": "user", "content": "hi"}])

    assert calls["n"] == providers.REQUEST_ATTEMPTS
