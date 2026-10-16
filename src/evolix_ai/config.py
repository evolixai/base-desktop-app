"""Runtime configuration read from a ``.env`` file and the environment.

Values are loaded once at startup via :func:`load_env`. Real environment
variables always take precedence over the ``.env`` file, and unknown or
missing values fall back to the defaults defined here.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

LOG_LEVEL_ENV = "LOG_LEVEL"
BASE_API_URL_ENV = "BASE_API_URL"

DEFAULT_LOG_LEVEL = logging.INFO

_ENV_FILENAME = ".env"
_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def _bundled_app_dir() -> Path:
    """Directory holding the packaged app, i.e. beside the ``.app`` on macOS."""
    exe = Path(sys.executable).resolve()
    parents = exe.parents
    if len(parents) >= 4 and parents[0].name == "MacOS" and parents[1].name == "Contents":
        return parents[3]
    return exe.parent


def env_path() -> Path:
    """Location of the ``.env`` file: beside the app when frozen, else CWD."""
    base = _bundled_app_dir() if getattr(sys, "frozen", False) else Path.cwd()
    return base / _ENV_FILENAME


def load_env(path: Path | None = None) -> Path | None:
    """Load variables from the ``.env`` file without overriding the environment.

    Returns the loaded path, or ``None`` when no file is present.
    """
    target = path or env_path()
    if target.is_file():
        load_dotenv(target, override=False)
        return target
    return None


def log_level() -> int:
    """Logging level from ``LOG_LEVEL``, defaulting to INFO for unknown values."""
    name = (os.environ.get(LOG_LEVEL_ENV) or "").strip().upper()
    return _LEVELS.get(name, DEFAULT_LOG_LEVEL)


def base_api_url() -> str:
    """Default base URL for the Custom provider preset, or an empty string."""
    return (os.environ.get(BASE_API_URL_ENV) or "").strip()
