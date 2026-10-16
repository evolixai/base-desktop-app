from __future__ import annotations

import pytest

from evolix_ai import i18n


def test_default_language_is_english() -> None:
    assert i18n.DEFAULT_LANGUAGE == "en"
    assert i18n.current_language() == "en"


def test_translates_to_english_and_vietnamese() -> None:
    i18n.set_language("en")
    assert i18n.tr("action.open") == "Open"
    i18n.set_language("vi")
    assert i18n.tr("action.open") == "Mở"


def test_unknown_language_falls_back_to_english() -> None:
    assert i18n.set_language("de") == "en"
    assert i18n.current_language() == "en"


def test_missing_key_returns_the_key() -> None:
    assert i18n.tr("does.not.exist") == "does.not.exist"


def test_formats_placeholders() -> None:
    i18n.set_language("en")
    assert i18n.tr("common.error", message="boom") == "Error: boom"
    i18n.set_language("vi")
    assert i18n.tr("common.error", message="boom") == "Lỗi: boom"


def test_plural_picks_the_right_form() -> None:
    i18n.set_language("en")
    assert i18n.trn("main.project_count", 1) == "1 project"
    assert i18n.trn("main.project_count", 2) == "2 projects"
    i18n.set_language("vi")
    assert i18n.trn("main.project_count", 2) == "2 dự án"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("vi_VN", "vi"),
        ("vi-VN", "vi"),
        ("en_US", "en"),
        ("fr_FR", "en"),
        ("", "en"),
        (None, "en"),
    ],
)
def test_normalize_language(name: str | None, expected: str) -> None:
    assert i18n.normalize_language(name) == expected


def test_catalogs_have_matching_keys() -> None:
    english = set(i18n._CATALOG["en"])
    for code, catalog in i18n._CATALOG.items():
        assert set(catalog) == english, f"key mismatch in '{code}'"


def test_available_languages_lists_english_and_vietnamese() -> None:
    codes = [code for code, _ in i18n.available_languages()]
    assert codes == ["en", "vi"]
