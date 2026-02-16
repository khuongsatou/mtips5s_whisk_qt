"""
Prompt Normalizer — sanitize prompts before adding to queue.

Plain text prompts: strip special characters, normalize whitespace.
JSON prompts: validate, re-serialize with proper formatting.
"""
import json
import re
import logging
import unicodedata

logger = logging.getLogger("whisk.prompt_normalizer")

# Characters explicitly allowed beyond alphanumeric + whitespace
_ALLOWED_PUNCTUATION = set(".,;:!?'\"-—–()[]{}/@#&*+=<>…")


def _is_safe_char(ch: str) -> bool:
    """Check if a character is safe for a plain-text prompt."""
    if ch.isascii():
        return ch.isalnum() or ch.isspace() or ch in _ALLOWED_PUNCTUATION
    # Keep non-ASCII letters/numbers (e.g. Vietnamese, CJK)
    cat = unicodedata.category(ch)
    return cat.startswith("L") or cat.startswith("N") or cat == "Zs"


# Multiple whitespace → single space (but preserve newlines)
_MULTI_SPACE = re.compile(r"[^\S\n]+")


class PromptNormalizer:
    """Normalize and sanitize prompts before queue insertion."""

    @staticmethod
    def is_json_prompt(text: str) -> bool:
        """Check if the text is a JSON prompt (object or array)."""
        stripped = text.strip()
        if not stripped:
            return False
        # Must start with { or [ AND end with } or ]
        if not ((stripped[0] == "{" and stripped[-1] == "}") or
                (stripped[0] == "[" and stripped[-1] == "]")):
            return False
        # Accept both valid JSON and JSON-like structures
        try:
            json.loads(stripped)
            return True
        except (json.JSONDecodeError, ValueError):
            # Still looks like JSON (has matching brackets), try to fix
            fixed = re.sub(r",\s*([}\]])", r"\1", stripped)
            try:
                json.loads(fixed)
                return True
            except (json.JSONDecodeError, ValueError):
                return False

    @staticmethod
    def normalize_json(text: str) -> str:
        """
        Parse and re-serialize JSON prompt.
        Ensures valid JSON with consistent formatting.
        Strips any trailing commas or control characters.
        """
        stripped = text.strip()
        try:
            parsed = json.loads(stripped)
            return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON prompt parse error: {e}")
            fixed = stripped
            # Remove trailing commas before } or ]
            fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
            # Remove BOM
            fixed = fixed.lstrip("\ufeff")
            try:
                parsed = json.loads(fixed)
                return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
            except json.JSONDecodeError:
                logger.error("❌ Cannot fix JSON prompt, returning as-is")
                return stripped

    @staticmethod
    def normalize_plain(text: str) -> str:
        """
        Sanitize plain-text prompt:
        - Remove problematic special characters (emoji, symbols, etc.)
        - Keep Vietnamese/CJK characters
        - Normalize whitespace (collapse multiple spaces)
        - Strip leading/trailing whitespace
        """
        result = "".join(ch for ch in text if _is_safe_char(ch))
        # Collapse multiple spaces (but keep single newlines)
        result = _MULTI_SPACE.sub(" ", result)
        # Strip each line
        result = "\n".join(line.strip() for line in result.splitlines())
        return result.strip()

    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Auto-detect prompt type and normalize accordingly.
        - JSON prompt → validate & re-serialize
        - Plain text → strip special chars & normalize whitespace
        """
        text = text.strip()
        if not text:
            return ""

        if cls.is_json_prompt(text):
            logger.info(f"📋 Normalizing JSON prompt ({len(text)} chars)")
            return cls.normalize_json(text)
        else:
            logger.info(f"📝 Normalizing plain prompt ({len(text)} chars)")
            return cls.normalize_plain(text)
