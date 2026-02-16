"""
Tests for Cookie / API-Key API integration (models + mock API).
"""
import pytest
from app.api.mock_api import MockApi
from app.api.models import ApiKeyItem, ApiResponse


class TestApiKeyItem:
    """Tests for ApiKeyItem dataclass."""

    def test_defaults(self):
        item = ApiKeyItem()
        assert item.provider == "WHISK"
        assert item.status == "active"
        assert item.error is False

    def test_to_dict_roundtrip(self):
        item = ApiKeyItem(
            id=4298,
            label="WHISK - test@example.com",
            provider="WHISK",
            flow_id=122,
        )
        d = item.to_dict()
        restored = ApiKeyItem.from_dict(d)
        assert restored.id == 4298
        assert restored.label == "WHISK - test@example.com"
        assert restored.provider == "WHISK"
        assert restored.flow_id == 122

    def test_from_server_response(self):
        """Parse actual server response format."""
        server_data = {
            "id": 4298,
            "label": "VEO3_V2 - test@gmail.com - 2/15/2026",
            "value": "ya29.mock_token",
            "provider": "WHISK",
            "status": "active",
            "billing_type": "free",
            "credit": 0.0,
            "requests": 0,
            "limit_requests": 0,
            "flow_id": 122,
            "user_id": 246,
            "error": False,
            "msg_error": None,
            "expired": "2026-02-15T23:17:16",
            "deleted_at": None,
            "metadata": {
                "cookies": {"__Secure-next-auth.session-token": "xxx"},
                "user_email": "test@gmail.com",
                "user_name": "Test User",
            },
            "createdAt": "2026-02-15T16:19:15",
        }
        item = ApiKeyItem.from_dict(server_data)
        assert item.id == 4298
        assert item.provider == "WHISK"
        assert item.flow_id == 122
        assert item.metadata["user_email"] == "test@gmail.com"
        assert item.expired == "2026-02-15T23:17:16"


class TestMockCookieApi:
    """Tests for mock cookie/api-key API methods."""

    @pytest.fixture
    def api(self):
        return MockApi()

    def test_test_server_cookie(self, api):
        resp = api.test_server_cookie({
            "cookies": {"__Secure-next-auth.session-token": "xxx"},
            "label": "Test",
            "flow_id": 122,
            "provider": "WHISK",
        })
        assert resp.success is True
        assert resp.data["ok"] is True
        assert resp.data["status"] == "active"
        assert resp.data["provider_info"]["token_match"] is True

    def test_save_server_cookie(self, api):
        resp = api.save_server_cookie({
            "cookies": {"__Secure-next-auth.session-token": "xxx"},
            "label": "WHISK - test@gmail.com",
            "flow_id": 122,
            "create_new": True,
        })
        assert resp.success is True
        assert resp.data["status"] == "ok"
        assert "api_key" in resp.data
        assert resp.data["api_key"]["provider"] == "WHISK"
        assert resp.data["api_key"]["flow_id"] == 122

    def test_get_api_keys_empty(self, api):
        resp = api.get_api_keys(flow_id=122)
        assert resp.success is True
        assert resp.data["items"] == []
        assert resp.data["total"] == 0

    def test_get_api_keys_after_save(self, api):
        api.save_server_cookie({
            "cookies": {"token": "abc"},
            "label": "key1",
            "flow_id": 122,
            "provider": "WHISK",
        })
        api.save_server_cookie({
            "cookies": {"token": "def"},
            "label": "key2",
            "flow_id": 122,
            "provider": "WHISK",
        })
        api.save_server_cookie({
            "cookies": {"token": "ghi"},
            "label": "other",
            "flow_id": 999,
            "provider": "WHISK",
        })

        resp = api.get_api_keys(flow_id=122, provider="WHISK")
        assert resp.success is True
        assert resp.data["total"] == 2
        assert len(resp.data["items"]) == 2

    def test_get_api_keys_provider_filter(self, api):
        api.save_server_cookie({
            "cookies": {},
            "label": "w1",
            "flow_id": 1,
            "provider": "WHISK",
        })
        api.save_server_cookie({
            "cookies": {},
            "label": "v1",
            "flow_id": 1,
            "provider": "OTHER",
        })

        whisk = api.get_api_keys(flow_id=1, provider="WHISK")
        assert whisk.data["total"] == 1
        assert whisk.data["items"][0]["provider"] == "WHISK"

    def test_delete_api_key(self, api):
        resp = api.save_server_cookie({
            "cookies": {},
            "label": "to_delete",
            "flow_id": 1,
            "provider": "WHISK",
        })
        key_id = resp.data["api_key"]["id"]

        del_resp = api.delete_api_key(key_id)
        assert del_resp.success is True
        assert del_resp.data["ok"] is True

        # Verify it's gone
        list_resp = api.get_api_keys(flow_id=1, provider="WHISK")
        assert list_resp.data["total"] == 0

    def test_delete_api_key_not_found(self, api):
        resp = api.delete_api_key(99999)
        assert resp.success is False
        assert "not found" in resp.message.lower()
