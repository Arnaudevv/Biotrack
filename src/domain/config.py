# =============================================================================
# PROJECT CONFIGURATION & ENVIRONMENT MANAGER
# =============================================================================
# This module manages environment variable loading and configuration mapping.
# It ensures the application remains portable and secure across different
# execution contexts (scripts, notebooks, or automated tasks).
# =============================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# PROJECT ROOT RESOLUTION
# Walks up from this file's location until it finds the .env anchor file.
# This is robust against file reorganization — never counts parent levels manually.
def find_project_root(anchor: str = ".env") -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / anchor).exists():
            return parent
    raise FileNotFoundError(
        f"Project root not found. No '{anchor}' file located in any parent directory."
    )

BASE_DIR = find_project_root()
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

# ENVIRONMENT SELECTION
# Defaults to 'development' if no ENVIRONMENT variable is set.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# DB URL BUILDER
# SQLite environments use a filename from .env and build an absolute URL here.
# PostgreSQL environments use a full URL stored directly in .env.
def _build_sqlite_url(env_var: str) -> str:
    filename = os.getenv(env_var)
    if not filename:
        return None
    db_path = BASE_DIR / "data" / filename
    return f"sqlite:///{db_path}"


# DATABASE URL MAPPING
DB_URL = {
    "development": _build_sqlite_url("DB_FILENAME_DEVELOPMENT"),
    "test":        _build_sqlite_url("DB_FILENAME_TEST"),
    "production":  os.getenv("DB_URL_PRODUCTION"),
}.get(ENVIRONMENT)


# CRITICAL SYSTEM CHECK
if not DB_URL:
    raise ValueError(
        f"CRITICAL ERROR: Database configuration missing.\n"
        f"Verified .env location: {ENV_PATH}\n"
        f"Active Environment: {ENVIRONMENT}\n"
    )

print(f"✅ Configuration loaded: {ENVIRONMENT} -> {DB_URL}")