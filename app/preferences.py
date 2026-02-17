"""
Whisk Desktop — User Preferences Persistence.

Saves/loads user preferences (theme, language) to ~/.whisk_preferences.json.
"""
import json
import os
import logging

logger = logging.getLogger("whisk.preferences")

PREFS_FILE = os.path.join(os.path.expanduser("~"), ".whisk_preferences.json")

DEFAULTS = {
    "theme": "dark",
    "language": "vi",
}


def load_preferences() -> dict:
    """Load preferences from disk, falling back to defaults."""
    try:
        if os.path.exists(PREFS_FILE):
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults for any missing keys
            merged = {**DEFAULTS, **data}
            logger.debug(f"📂 Loaded preferences: {merged}")
            return merged
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"⚠️ Failed to load preferences: {e}")
    return dict(DEFAULTS)


def save_preferences(prefs: dict) -> None:
    """Save preferences to disk."""
    try:
        with open(PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)
        logger.debug(f"💾 Saved preferences: {prefs}")
    except OSError as e:
        logger.warning(f"⚠️ Failed to save preferences: {e}")


def save_preference(key: str, value: str) -> None:
    """Save a single preference key."""
    prefs = load_preferences()
    prefs[key] = value
    save_preferences(prefs)
