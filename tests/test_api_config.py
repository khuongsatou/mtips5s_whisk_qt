"""
Tests for api_config — URL builders and environment config.
"""
import os
import pytest
from app.api.api_config import admin_url, labs_url, flow_url, ADMIN_BASE_URL, LABS_BASE_URL, FLOW_BASE_URL


class TestUrlBuilders:
    """Test URL builder functions."""

    def test_admin_url_simple(self):
        result = admin_url("api-keys")
        assert result.endswith("/api-keys")
        assert ADMIN_BASE_URL in result

    def test_admin_url_strips_leading_slash(self):
        r1 = admin_url("/api-keys")
        r2 = admin_url("api-keys")
        assert r1 == r2

    def test_admin_url_nested_path(self):
        result = admin_url("api-keys/42/refresh")
        assert "/api-keys/42/refresh" in result

    def test_labs_url_simple(self):
        result = labs_url("fx/api/trpc/media.createOrUpdateWorkflow")
        assert LABS_BASE_URL in result

    def test_labs_url_strips_leading_slash(self):
        r1 = labs_url("/fx/api")
        r2 = labs_url("fx/api")
        assert r1 == r2

    def test_flow_url_simple(self):
        result = flow_url("flows")
        assert result.endswith("/flows")
        assert FLOW_BASE_URL in result

    def test_flow_url_strips_leading_slash(self):
        r1 = flow_url("/flows")
        r2 = flow_url("flows")
        assert r1 == r2

    def test_flow_url_with_id(self):
        result = flow_url("flows/123")
        assert "/flows/123" in result


class TestBaseUrls:
    """Test base URL constants are set."""

    def test_admin_base_url_not_empty(self):
        assert ADMIN_BASE_URL != ""

    def test_labs_base_url_set(self):
        assert "labs.google" in LABS_BASE_URL

    def test_flow_base_url_not_empty(self):
        assert FLOW_BASE_URL != ""


class TestFallbackDotenvLoader:
    """Test the fallback load_dotenv function."""

    def test_load_nonexistent_file(self):
        """Fallback loader should handle missing files gracefully."""
        from app.api.api_config import load_dotenv
        # Should not raise
        load_dotenv(dotenv_path="/tmp/nonexistent_env_file_12345")

    def test_load_env_file(self, tmp_path):
        """Fallback loader parses KEY=VALUE pairs."""
        from app.api.api_config import load_dotenv
        env_file = tmp_path / ".env.test"
        env_file.write_text("TEST_WHISK_KEY=hello_world\n# comment\n\nFOO=bar\n")

        # Remove keys if they exist
        os.environ.pop("TEST_WHISK_KEY", None)
        os.environ.pop("FOO", None)

        load_dotenv(dotenv_path=str(env_file), override=True)

        assert os.environ.get("TEST_WHISK_KEY") == "hello_world"
        assert os.environ.get("FOO") == "bar"

        # Cleanup
        os.environ.pop("TEST_WHISK_KEY", None)
        os.environ.pop("FOO", None)

    def test_override_false_preserves_existing(self, tmp_path):
        """override=False should not overwrite existing env vars."""
        from app.api.api_config import load_dotenv
        env_file = tmp_path / ".env.test2"
        env_file.write_text("TEST_OVERRIDE_KEY=new\n")

        os.environ["TEST_OVERRIDE_KEY"] = "original"

        load_dotenv(dotenv_path=str(env_file), override=False)

        assert os.environ["TEST_OVERRIDE_KEY"] == "original"

        # Cleanup
        os.environ.pop("TEST_OVERRIDE_KEY", None)
