from evolix_ai.ui.browser_tab import normalize_url


def test_normalize_url_infers_https() -> None:
    url = normalize_url("example.com")
    assert url.scheme() == "http"
    assert url.host() == "example.com"


def test_normalize_url_keeps_explicit_scheme() -> None:
    url = normalize_url("https://opencode.ai/docs")
    assert url.scheme() == "https"
    assert url.host() == "opencode.ai"


def test_normalize_url_keeps_about_pages() -> None:
    assert normalize_url("about:blank").scheme() == "about"
