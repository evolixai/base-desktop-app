from __future__ import annotations

import logging
import sys
from pathlib import Path

from evolix_ai import config


def test_load_env_applies_file_values(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("LOG_LEVEL=DEBUG\nBASE_API_URL=https://example.test/v1\n", encoding="utf-8")
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("BASE_API_URL", raising=False)

    loaded = config.load_env(env_file)

    assert loaded == env_file
    assert config.log_level() == logging.DEBUG
    assert config.base_api_url() == "https://example.test/v1"


def test_load_env_does_not_override_real_environment(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("LOG_LEVEL=DEBUG\n", encoding="utf-8")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    config.load_env(env_file)

    assert config.log_level() == logging.WARNING


def test_load_env_missing_file_returns_none(tmp_path: Path) -> None:
    assert config.load_env(tmp_path / "missing.env") is None


def test_env_path_uses_cwd_when_not_frozen(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.chdir(tmp_path)

    assert config.env_path() == tmp_path / ".env"


def test_env_path_is_beside_executable_when_frozen(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "Evolix AI"))

    assert config.env_path() == tmp_path / ".env"


def test_env_path_skips_macos_bundle(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        sys, "executable", str(tmp_path / "Evolix AI.app" / "Contents" / "MacOS" / "Evolix AI")
    )

    assert config.env_path() == tmp_path / ".env"


def test_log_level_defaults_and_maps_names(monkeypatch) -> None:
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert config.log_level() == logging.INFO

    monkeypatch.setenv("LOG_LEVEL", "warning")
    assert config.log_level() == logging.WARNING

    monkeypatch.setenv("LOG_LEVEL", "bogus")
    assert config.log_level() == logging.INFO


def test_base_api_url_defaults_to_empty_and_trims(monkeypatch) -> None:
    monkeypatch.delenv("BASE_API_URL", raising=False)
    assert config.base_api_url() == ""

    monkeypatch.setenv("BASE_API_URL", "  https://x.test/v1  ")
    assert config.base_api_url() == "https://x.test/v1"
