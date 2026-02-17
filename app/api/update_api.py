"""
Whisk Desktop — Update API Client.

Checks the admin server for the latest application version.
"""
import json
import logging
import urllib.request
import urllib.error

from app.api.api_config import ADMIN_BASE_URL

logger = logging.getLogger("whisk.update_api")


def check_for_update(current_version: str, timeout: int = 10) -> dict:
    """Check the admin server for the latest version.

    Args:
        current_version: The currently running version string (e.g. "1.0.0").
        timeout: HTTP request timeout in seconds.

    Returns:
        dict with keys:
          - has_update (bool)
          - latest_version (str)
          - download_url (str)
          - changelog (str)
          - error (str | None)
    """
    url = f"{ADMIN_BASE_URL}/app/version"
    logger.info(f"🔄 Checking for updates at {url}")

    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest = data.get("version", current_version)
        download_url = data.get("download_url", "")
        changelog = data.get("changelog", "")

        has_update = _compare_versions(current_version, latest)

        logger.info(
            f"✅ Version check: current={current_version}, "
            f"latest={latest}, has_update={has_update}"
        )

        return {
            "has_update": has_update,
            "latest_version": latest,
            "download_url": download_url,
            "changelog": changelog,
            "error": None,
        }

    except urllib.error.URLError as e:
        logger.warning(f"⚠️ Update check failed: {e}")
        return {
            "has_update": False,
            "latest_version": current_version,
            "download_url": "",
            "changelog": "",
            "error": str(e),
        }
    except Exception as e:
        logger.warning(f"⚠️ Update check error: {e}")
        return {
            "has_update": False,
            "latest_version": current_version,
            "download_url": "",
            "changelog": "",
            "error": str(e),
        }


def _compare_versions(current: str, latest: str) -> bool:
    """Return True if latest is strictly newer than current.

    Compares semantic version tuples (major, minor, patch).
    """
    try:
        cur_parts = tuple(int(x) for x in current.split("."))
        lat_parts = tuple(int(x) for x in latest.split("."))
        return lat_parts > cur_parts
    except (ValueError, AttributeError):
        return False
