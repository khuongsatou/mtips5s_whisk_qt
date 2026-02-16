"""
Tests for FlowApiClient — flow CRUD with mocked HTTP.
"""
import json
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from app.api.flow_api import FlowApiClient


def _mock_response(body: dict, status: int = 200):
    """Create a mock urllib response."""
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_http_error(code: int, body: dict | str = ""):
    """Create a mock HTTPError."""
    import urllib.error
    if isinstance(body, dict):
        body = json.dumps(body)
    resp = BytesIO(body.encode("utf-8"))
    return urllib.error.HTTPError(
        url="http://test", code=code, msg="Error", hdrs={}, fp=resp,
    )


class TestFlowApiClientInit:
    """Test initialization."""

    def test_default_access_token(self):
        client = FlowApiClient()
        assert client._access_token == ""

    def test_custom_access_token(self):
        client = FlowApiClient(access_token="tok-123")
        assert client._access_token == "tok-123"

    def test_set_access_token(self):
        client = FlowApiClient()
        client.set_access_token("new-tok")
        assert client._access_token == "new-tok"

    def test_headers_without_content_type(self):
        client = FlowApiClient(access_token="tok")
        h = client._headers()
        assert h["Authorization"] == "Bearer tok"
        assert "Content-Type" not in h

    def test_headers_with_content_type(self):
        client = FlowApiClient(access_token="tok")
        h = client._headers(with_content_type=True)
        assert h["Content-Type"] == "application/json"


class TestFlowApiCreateFlow:
    """Test create_flow method."""

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_create_flow_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"id": 42, "name": "test"})
        client = FlowApiClient(access_token="tok")

        result = client.create_flow({"name": "test"})

        assert result.success is True
        assert result.data["id"] == 42

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_create_flow_adds_default_type(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"id": 1})
        client = FlowApiClient(access_token="tok")

        data = {"name": "test"}
        client.create_flow(data)

        assert data["type"] == "WHISK"

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_create_flow_preserves_custom_type(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"id": 1})
        client = FlowApiClient(access_token="tok")

        data = {"name": "test", "type": "CUSTOM"}
        client.create_flow(data)

        assert data["type"] == "CUSTOM"

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_create_flow_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(400, {"message": "Bad request"})
        client = FlowApiClient(access_token="tok")

        result = client.create_flow({"name": "test"})

        assert result.success is False
        assert "Bad request" in result.message

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_create_flow_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        client = FlowApiClient(access_token="tok")

        result = client.create_flow({"name": "test"})

        assert result.success is False
        assert "Cannot connect" in result.message

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_create_flow_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Unexpected")
        client = FlowApiClient(access_token="tok")

        result = client.create_flow({"name": "test"})

        assert result.success is False
        assert "Unexpected" in result.message


class TestFlowApiGetFlows:
    """Test get_flows method."""

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_get_flows_success(self, mock_urlopen):
        body = {"items": [{"id": 1}, {"id": 2}], "total": 2}
        mock_urlopen.return_value = _mock_response(body)
        client = FlowApiClient(access_token="tok")

        result = client.get_flows()

        assert result.success is True
        assert len(result.data["items"]) == 2
        assert result.total == 2

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_get_flows_empty(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"items": [], "total": 0})
        client = FlowApiClient(access_token="tok")

        result = client.get_flows()

        assert result.success is True
        assert result.data["items"] == []

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_get_flows_with_pagination(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"items": [], "total": 50})
        client = FlowApiClient(access_token="tok")

        result = client.get_flows(offset=20, limit=10)

        assert result.success is True
        # Verify URL contains pagination params
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert "offset=20" in req.full_url
        assert "limit=10" in req.full_url

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_get_flows_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(500, {"message": "Server error"})
        client = FlowApiClient(access_token="tok")

        result = client.get_flows()

        assert result.success is False

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_get_flows_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        client = FlowApiClient(access_token="tok")

        result = client.get_flows()

        assert result.success is False

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_get_flows_total_fallback(self, mock_urlopen):
        # No 'total' key, should fallback to len(items)
        mock_urlopen.return_value = _mock_response({"items": [{"id": 1}]})
        client = FlowApiClient(access_token="tok")

        result = client.get_flows()

        assert result.total == 1


class TestFlowApiDeleteFlow:
    """Test delete_flow method."""

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_delete_flow_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"ok": True})
        client = FlowApiClient(access_token="tok")

        result = client.delete_flow(42)

        assert result.success is True

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_delete_flow_not_ok(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"ok": False})
        client = FlowApiClient(access_token="tok")

        result = client.delete_flow(42)

        assert result.success is False

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_delete_flow_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(404, {"message": "Not found"})
        client = FlowApiClient(access_token="tok")

        result = client.delete_flow(999)

        assert result.success is False
        assert "Not found" in result.message

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_delete_flow_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        client = FlowApiClient(access_token="tok")

        result = client.delete_flow(1)

        assert result.success is False

    @patch("app.api.flow_api.urllib.request.urlopen")
    def test_delete_flow_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("boom")
        client = FlowApiClient(access_token="tok")

        result = client.delete_flow(1)

        assert result.success is False


class TestFlowApiHandleHttpError:
    """Test _handle_http_error helper."""

    def test_parses_json_error(self):
        client = FlowApiClient()
        err = _make_http_error(422, {"message": "Validation failed"})
        result = client._handle_http_error(err, "test_method")
        assert result.success is False
        assert "Validation failed" in result.message

    def test_non_json_error_body(self):
        client = FlowApiClient()
        err = _make_http_error(500, "Internal Server Error")
        result = client._handle_http_error(err, "test_method")
        assert result.success is False
        assert "500" in result.message
