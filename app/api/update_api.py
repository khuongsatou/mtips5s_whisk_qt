"""
Whisk Desktop — Update API Client.

Checks the admin server for the latest application version.
Endpoint: POST /auth/check-update
"""
import json
import logging
import sys
import urllib.request
import urllib.error

from app.api.api_config import ADMIN_BASE_URL

logger = logging.getLogger("whisk.update_api")


def _get_platform() -> str:
    """Return 'macos' or 'windows' based on current OS."""
    if sys.platform == "darwin":
        return "macos"
    return "windows"


def check_for_update(current_version: str, timeout: int = 10) -> dict:
    """Check the admin server for the latest version.

    Sends POST /auth/check-update with current_version and platform.

    Returns:
        dict with keys:
          - has_update (bool)
          - latest_version (str)
          - download_url (str)
          - file_name (str)
          - changelog (list[dict])  — [{version, date, changes}, ...]
          - force_update (bool)
          - error (str | None)
    """
    url = f"{ADMIN_BASE_URL}/auth/check-update"
    payload = json.dumps({
        "current_version": current_version,
        "platform": _get_platform(),
    }).encode("utf-8")

    logger.info(f"🔄 Checking for updates at {url}")

    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        result = {
            "has_update": data.get("has_update", False),
            "latest_version": data.get("latest_version", current_version),
            "download_url": data.get("download_url", ""),
            "file_name": data.get("file_name", ""),
            "changelog": data.get("changelog", []),
            "force_update": data.get("force_update", False),
            "error": None,
        }

        logger.info(
            f"✅ Version check: current={current_version}, "
            f"latest={result['latest_version']}, "
            f"has_update={result['has_update']}"
        )
        return result

    except urllib.error.URLError as e:
        logger.warning(f"⚠️ Update check failed: {e}")
        return _error_result(current_version, str(e))
    except Exception as e:
        logger.warning(f"⚠️ Update check error: {e}")
        return _error_result(current_version, str(e))


def _error_result(current_version: str, error: str) -> dict:
    return {
        "has_update": False,
        "latest_version": current_version,
        "download_url": "",
        "file_name": "",
        "changelog": [],
        "force_update": False,
        "error": error,
    }
