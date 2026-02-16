"""
Whisk Desktop — API Configuration.

Centralized base URL registry for all API endpoints.
Loads from .env / .env.dev / .env.prod based on APP_ENV.
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger("whisk.api_config")

# ── Locate project root & load .env ──────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

try:
    from dotenv import load_dotenv
except ImportError:
    # Minimal fallback: parse KEY=VALUE lines from .env manually
    def load_dotenv(dotenv_path=None, override=False):
        if dotenv_path and Path(dotenv_path).exists():
            with open(dotenv_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, value = line.partition("=")
                        key, value = key.strip(), value.strip()
                        if override or key not in os.environ:
                            os.environ[key] = value

# 1. Load root .env first (sets APP_ENV)
_root_env = _PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=str(_root_env), override=False)

# 2. Determine environment
APP_ENV = os.environ.get("APP_ENV", "dev")

# 3. Load environment-specific file (.env.dev or .env.prod), overriding
_env_file = _PROJECT_ROOT / f".env.{APP_ENV}"
if _env_file.exists():
    load_dotenv(dotenv_path=str(_env_file), override=True)
    logger.info(f"📋 Loaded config from {_env_file.name} (APP_ENV={APP_ENV})")
else:
    logger.warning(f"⚠️ .env.{APP_ENV} not found, using defaults")

# ── Base URLs (from env vars or defaults) ─────────────────────────────

# Admin API — user management, authentication, settings
ADMIN_BASE_URL = os.environ.get(
    "ADMIN_BASE_URL",
    "https://tools.1nutnhan.com" if APP_ENV == "prod" else "http://localhost:8000",
)

# Labs API — direct image creation operations
LABS_BASE_URL = os.environ.get("LABS_BASE_URL", "https://labs.google/fx")

# Flow API — flow/project management
FLOW_BASE_URL = os.environ.get(
    "FLOW_BASE_URL",
    "https://tools.1nutnhan.com" if APP_ENV == "prod" else "http://localhost:8000",
)

logger.info(f"⚙️ API Config: ENV={APP_ENV} | ADMIN={ADMIN_BASE_URL} | FLOW={FLOW_BASE_URL}")


def admin_url(path: str) -> str:
    """Build a full URL for the admin API."""
    return f"{ADMIN_BASE_URL}/{path.lstrip('/')}"


def labs_url(path: str) -> str:
    """Build a full URL for the labs API."""
    return f"{LABS_BASE_URL}/{path.lstrip('/')}"


def flow_url(path: str) -> str:
    """Build a full URL for the flow API."""
    return f"{FLOW_BASE_URL}/{path.lstrip('/')}"
