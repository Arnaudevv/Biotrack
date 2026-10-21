"""Project configuration loader for the server side."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency in clean clones
    def load_dotenv(dotenv_path=None):
        return False


def find_project_root(anchor: str = "alembic.ini") -> Path:
    """Walk upward from the current file until a versioned project anchor is found."""
    current = Path(__file__).resolve().parent
    for parent in (current, *current.parents):
        if (parent / anchor).exists():
            return parent
    raise FileNotFoundError(
        f"Project root not found. No '{anchor}' file in any parent directory."
    )


BASE_DIR = find_project_root()
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

DEFAULT_ENVIRONMENT = "development"
DEFAULT_DB_FILENAME_DEVELOPMENT = "biotrack.db"
DEFAULT_DB_FILENAME_TEST = "biotrack_test.db"

ENVIRONMENT = os.getenv("ENVIRONMENT", DEFAULT_ENVIRONMENT)


def _build_sqlite_url(env_var: str, fallback_filename: str) -> str:
    filename = os.getenv(env_var, fallback_filename)
    db_path = BASE_DIR / "data" / filename
    return f"sqlite:///{db_path}"


DB_URL = {
    "development": _build_sqlite_url(
        "DB_FILENAME_DEVELOPMENT",
        DEFAULT_DB_FILENAME_DEVELOPMENT,
    ),
    "test": _build_sqlite_url(
        "DB_FILENAME_TEST",
        DEFAULT_DB_FILENAME_TEST,
    ),
    "production": os.getenv("DB_URL_PRODUCTION"),
}.get(ENVIRONMENT, _build_sqlite_url(
    "DB_FILENAME_DEVELOPMENT",
    DEFAULT_DB_FILENAME_DEVELOPMENT,
))
