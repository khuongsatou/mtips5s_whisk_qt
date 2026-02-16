"""
Tests for Flow API integration (models + mock API).
"""
import pytest
from app.api.mock_api import MockApi
from app.api.models import FlowConfig, FlowItem, ApiResponse


class TestFlowConfig:
    """Tests for FlowConfig dataclass."""

    def test_defaults(self):
        config = FlowConfig()
        assert config.auto_generate is True
        assert config.seed is None
        assert config.aspectRatio == "VIDEO_ASPECT_RATIO_LANDSCAPE"
        assert config.videoModelKey == "veo_3_1_t2v_fast_ultra"
        assert config.batch_size == 5
        assert config.concurrent_limit == 3
        assert config.auto_download is True
        assert config.retry_failed is True
        assert config.max_retries == 2

    def test_to_dict_roundtrip(self):
        config = FlowConfig(batch_size=10, seed=42)
        d = config.to_dict()
        restored = FlowConfig.from_dict(d)
        assert restored.batch_size == 10
        assert restored.seed == 42
        assert restored.auto_generate is True

    def test_from_dict_partial(self):
        config = FlowConfig.from_dict({"batch_size": 3})
        assert config.batch_size == 3
        assert config.max_retries == 2  # default


class TestFlowItem:
    """Tests for FlowItem dataclass."""

    def test_defaults(self):
        flow = FlowItem()
        assert flow.type == "WHISK"
        assert flow.status == "pending"
        assert flow.upload_count == 0

    def test_to_dict_roundtrip(self):
        flow = FlowItem(id=42, name="test_flow", type="WHISK")
        d = flow.to_dict()
        restored = FlowItem.from_dict(d)
        assert restored.id == 42
        assert restored.name == "test_flow"
        assert restored.type == "WHISK"
        assert isinstance(restored.config, FlowConfig)

    def test_from_server_response(self):
        """Parse actual server response format."""
        server_data = {
            "id": 122,
            "name": "flow_4",
            "description": "Video generation project",
            "type": "WHISK",
            "status": "pending",
            "config": {
                "aspectRatio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
                "auto_download": True,
                "auto_generate": True,
                "batch_size": 5,
                "concurrent_limit": 3,
                "max_retries": 2,
                "retry_failed": True,
                "seed": None,
                "videoModelKey": "veo_3_1_t2v_fast_ultra",
            },
            "created_at": "2026-02-15T16:17:40",
            "upload_count": 0,
            "user_id": 246,
        }
        flow = FlowItem.from_dict(server_data)
        assert flow.id == 122
        assert flow.name == "flow_4"
        assert flow.type == "WHISK"
        assert flow.config.batch_size == 5
        assert flow.config.videoModelKey == "veo_3_1_t2v_fast_ultra"
        assert flow.upload_count == 0


class TestMockFlowApi:
    """Tests for mock flow API methods."""

    @pytest.fixture
    def api(self):
        return MockApi()

    def test_create_flow(self, api):
        resp = api.create_flow({
            "name": "test_flow",
            "description": "Test flow",
            "type": "WHISK",
            "config": {"batch_size": 3},
        })
        assert resp.success is True
        assert resp.data["name"] == "test_flow"
        assert resp.data["type"] == "WHISK"
        assert resp.data["config"]["batch_size"] == 3
        assert resp.data["status"] == "pending"

    def test_create_flow_default_type(self, api):
        resp = api.create_flow({"name": "no_type"})
        assert resp.success is True
        assert resp.data["type"] == "WHISK"

    def test_get_flows_empty(self, api):
        resp = api.get_flows()
        assert resp.success is True
        assert resp.data["items"] == []
        assert resp.data["total"] == 0

    def test_get_flows_after_create(self, api):
        api.create_flow({"name": "flow_1", "type": "WHISK"})
        api.create_flow({"name": "flow_2", "type": "WHISK"})
        api.create_flow({"name": "other", "type": "OTHER_TYPE"})

        resp = api.get_flows(flow_type="WHISK")
        assert resp.success is True
        assert resp.data["total"] == 2
        assert len(resp.data["items"]) == 2

    def test_get_flows_pagination(self, api):
        for i in range(5):
            api.create_flow({"name": f"flow_{i}", "type": "WHISK"})

        resp = api.get_flows(offset=0, limit=2, flow_type="WHISK")
        assert resp.data["total"] == 5
        assert len(resp.data["items"]) == 2
        assert resp.data["has_more"] is True

        resp2 = api.get_flows(offset=4, limit=2, flow_type="WHISK")
        assert len(resp2.data["items"]) == 1
        assert resp2.data["has_more"] is False

    def test_get_flows_type_filter(self, api):
        api.create_flow({"name": "w1", "type": "WHISK"})
        api.create_flow({"name": "v1", "type": "VEO3_V2"})

        whisk = api.get_flows(flow_type="WHISK")
        assert whisk.data["total"] == 1
        assert whisk.data["items"][0]["type"] == "WHISK"

        veo = api.get_flows(flow_type="VEO3_V2")
        assert veo.data["total"] == 1
        assert veo.data["items"][0]["type"] == "VEO3_V2"

    def test_delete_flow(self, api):
        resp = api.create_flow({"name": "to_delete", "type": "WHISK"})
        flow_id = resp.data["id"]

        del_resp = api.delete_flow(flow_id)
        assert del_resp.success is True
        assert del_resp.data["ok"] is True

        # Verify it's gone
        list_resp = api.get_flows(flow_type="WHISK")
        assert list_resp.data["total"] == 0

    def test_delete_flow_not_found(self, api):
        resp = api.delete_flow(99999)
        assert resp.success is False
        assert "not found" in resp.message.lower()
