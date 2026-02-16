"""
Tests for PromptNormalizer — plain text and JSON prompt sanitization.
"""
import json
import pytest
from app.prompt_normalizer import PromptNormalizer


class TestIsJsonPrompt:
    """Test JSON detection logic."""

    def test_valid_json_object(self):
        assert PromptNormalizer.is_json_prompt('{"key": "value"}') is True

    def test_valid_json_array(self):
        assert PromptNormalizer.is_json_prompt('[1, 2, 3]') is True

    def test_plain_text(self):
        assert PromptNormalizer.is_json_prompt("A cute cat sitting") is False

    def test_empty_string(self):
        assert PromptNormalizer.is_json_prompt("") is False

    def test_whitespace_only(self):
        assert PromptNormalizer.is_json_prompt("   ") is False

    def test_starts_with_brace_not_json(self):
        # Starts with { but doesn't end with }
        assert PromptNormalizer.is_json_prompt("{hello world") is False

    def test_trailing_comma_detected(self):
        # Trailing comma JSON should be detected as JSON-like
        assert PromptNormalizer.is_json_prompt('{"a": 1,}') is True

    def test_nested_json(self):
        data = json.dumps({"prompt": "hello", "settings": {"seed": 42}})
        assert PromptNormalizer.is_json_prompt(data) is True

    def test_json_with_whitespace(self):
        assert PromptNormalizer.is_json_prompt('  {"a": 1}  ') is True

    def test_number_not_json(self):
        assert PromptNormalizer.is_json_prompt("42") is False

    def test_string_not_json(self):
        assert PromptNormalizer.is_json_prompt('"hello"') is False


class TestNormalizeJson:
    """Test JSON normalization."""

    def test_valid_json_compacted(self):
        result = PromptNormalizer.normalize_json('{"prompt": "hello",  "seed": 42}')
        parsed = json.loads(result)
        assert parsed == {"prompt": "hello", "seed": 42}

    def test_trailing_comma_fixed(self):
        result = PromptNormalizer.normalize_json('{"a": 1, "b": 2,}')
        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": 2}

    def test_unicode_preserved(self):
        result = PromptNormalizer.normalize_json('{"text": "Cảnh đẹp Hà Nội"}')
        assert "Cảnh đẹp Hà Nội" in result

    def test_nested_json(self):
        input_json = '{"prompt": "test", "config": {"model": "v3", "seed": 123}}'
        result = PromptNormalizer.normalize_json(input_json)
        parsed = json.loads(result)
        assert parsed["config"]["model"] == "v3"

    def test_array_json(self):
        result = PromptNormalizer.normalize_json('[1, 2, 3]')
        assert json.loads(result) == [1, 2, 3]

    def test_invalid_json_returns_as_is(self):
        bad_json = '{not valid json at all}'
        result = PromptNormalizer.normalize_json(bad_json)
        assert result == bad_json.strip()

    def test_bom_stripped(self):
        bom_json = '\ufeff{"a": 1}'
        result = PromptNormalizer.normalize_json(bom_json)
        assert json.loads(result) == {"a": 1}


class TestNormalizePlain:
    """Test plain text normalization."""

    def test_clean_text_unchanged(self):
        text = "A beautiful sunset over the ocean"
        assert PromptNormalizer.normalize_plain(text) == text

    def test_strips_whitespace(self):
        assert PromptNormalizer.normalize_plain("  hello  ") == "hello"

    def test_collapses_multiple_spaces(self):
        assert PromptNormalizer.normalize_plain("a    b    c") == "a b c"

    def test_preserves_basic_punctuation(self):
        text = "Scene 1: A cat, a dog. Really? Yes!"
        result = PromptNormalizer.normalize_plain(text)
        assert ":" in result
        assert "," in result
        assert "." in result
        assert "?" in result
        assert "!" in result

    def test_preserves_vietnamese(self):
        text = "Cảnh đẹp của Hà Nội vào mùa thu"
        result = PromptNormalizer.normalize_plain(text)
        assert result == text

    def test_removes_emoji(self):
        text = "A 🎨 painting of 🌅 sunset"
        result = PromptNormalizer.normalize_plain(text)
        assert "🎨" not in result
        assert "🌅" not in result
        assert "painting" in result
        assert "sunset" in result

    def test_removes_trademark_symbols(self):
        text = "Product™ with ® and ©"
        result = PromptNormalizer.normalize_plain(text)
        assert "™" not in result
        assert "®" not in result
        assert "©" not in result

    def test_preserves_quotes(self):
        text = 'She said "hello" and \'goodbye\''
        result = PromptNormalizer.normalize_plain(text)
        assert '"hello"' in result
        assert "'goodbye'" in result

    def test_preserves_parentheses(self):
        text = "Photo (high quality) [detailed]"
        result = PromptNormalizer.normalize_plain(text)
        assert "(high quality)" in result
        assert "[detailed]" in result

    def test_empty_string(self):
        assert PromptNormalizer.normalize_plain("") == ""

    def test_line_stripping(self):
        text = "  line 1  \n  line 2  "
        result = PromptNormalizer.normalize_plain(text)
        assert result == "line 1\nline 2"


class TestNormalize:
    """Test auto-detection normalize()."""

    def test_auto_detects_json(self):
        json_text = '{"prompt": "test"}'
        result = PromptNormalizer.normalize(json_text)
        assert json.loads(result) == {"prompt": "test"}

    def test_auto_detects_plain(self):
        plain = "A cute cat sitting on a chair"
        result = PromptNormalizer.normalize(plain)
        assert result == plain

    def test_empty_returns_empty(self):
        assert PromptNormalizer.normalize("") == ""

    def test_whitespace_returns_empty(self):
        assert PromptNormalizer.normalize("   ") == ""

    def test_json_with_trailing_comma(self):
        result = PromptNormalizer.normalize('{"a": 1,}')
        assert json.loads(result) == {"a": 1}

    def test_plain_with_special_chars(self):
        result = PromptNormalizer.normalize("Hello™ World©")
        assert "™" not in result
        assert "©" not in result
        assert "Hello" in result
        assert "World" in result
