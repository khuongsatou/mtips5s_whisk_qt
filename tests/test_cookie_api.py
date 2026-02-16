"""
Tests for CookieApiClient — cookie/api-key CRUD with mocked HTTP.
"""
import json
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from app.api.cookie_api import CookieApiClient


def _mock_response(body: dict, status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_http_error(code: int, body: dict | str = ""):
    import urllib.error
    if isinstance(body, dict):
        body = json.dumps(body)
    return urllib.error.HTTPError(
        url="http://test", code=code, msg="Error",
        hdrs={}, fp=BytesIO(body.encode("utf-8")),
    )


class TestCookieApiInit:
    def test_default_token(self):
        c = CookieApiClient()
        assert c._access_token == ""

    def test_custom_token(self):
        c = CookieApiClient(access_token="tok")
        assert c._access_token == "tok"

    def test_set_access_token(self):
        c = CookieApiClient()
        c.set_access_token("new")
        assert c._access_token == "new"

    def test_headers(self):
        c = CookieApiClient(access_token="t")
        h = c._headers()
        assert "Bearer t" in h["Authorization"]

    def test_headers_with_content_type(self):
        c = CookieApiClient(access_token="t")
        h = c._headers(with_content_type=True)
        assert h["Content-Type"] == "application/json"


class TestCookieApiTestCookie:
    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_test_cookie_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "ok": True, "user_email": "test@test.com", "user_name": "Test",
        })
        c = CookieApiClient(access_token="tok")
        result = c.test_cookie({"cookies": {}, "label": "l", "flow_id": 1})
        assert result.success is True

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_test_cookie_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(401, {"message": "Unauthorized"})
        c = CookieApiClient(access_token="tok")
        result = c.test_cookie({"cookies": {}})
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_test_cookie_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        c = CookieApiClient(access_token="tok")
        result = c.test_cookie({"cookies": {}})
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_test_cookie_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("boom")
        c = CookieApiClient(access_token="tok")
        result = c.test_cookie({"cookies": {}})
        assert result.success is False


class TestCookieApiSaveCookie:
    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_save_cookie_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"id": 1, "status": "ok"})
        c = CookieApiClient(access_token="tok")
        result = c.save_cookie({"cookies": {}, "label": "l", "flow_id": 1})
        assert result.success is True

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_save_cookie_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(400, {"message": "Bad data"})
        c = CookieApiClient(access_token="tok")
        result = c.save_cookie({"cookies": {}})
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_save_cookie_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        c = CookieApiClient(access_token="tok")
        result = c.save_cookie({})
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_save_cookie_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("oops")
        c = CookieApiClient(access_token="tok")
        result = c.save_cookie({})
        assert result.success is False


class TestCookieApiGetApiKeys:
    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_get_api_keys_success(self, mock_urlopen):
        body = {"items": [{"id": 1}], "total": 1, "offset": 0, "limit": 1000}
        mock_urlopen.return_value = _mock_response(body)
        c = CookieApiClient(access_token="tok")
        result = c.get_api_keys(flow_id=1)
        assert result.success is True
        assert len(result.data["items"]) == 1

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_get_api_keys_empty(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"items": [], "total": 0})
        c = CookieApiClient(access_token="tok")
        result = c.get_api_keys(flow_id=1)
        assert result.success is True
        assert result.data["items"] == []

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_get_api_keys_with_filters(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"items": [], "total": 0})
        c = CookieApiClient(access_token="tok")
        c.get_api_keys(flow_id=5, status="active", mine=True)
        req = mock_urlopen.call_args[0][0]
        assert "flow_id=5" in req.full_url
        assert "status=active" in req.full_url

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_get_api_keys_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(500, {"message": "Server error"})
        c = CookieApiClient(access_token="tok")
        result = c.get_api_keys(flow_id=1)
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_get_api_keys_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        c = CookieApiClient(access_token="tok")
        result = c.get_api_keys(flow_id=1)
        assert result.success is False


class TestCookieApiDeleteApiKey:
    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_delete_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"ok": True})
        c = CookieApiClient(access_token="tok")
        result = c.delete_api_key(42)
        assert result.success is True

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_delete_not_ok(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"ok": False})
        c = CookieApiClient(access_token="tok")
        result = c.delete_api_key(42)
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_delete_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(404, {"message": "Not found"})
        c = CookieApiClient(access_token="tok")
        result = c.delete_api_key(999)
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_delete_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("refused")
        c = CookieApiClient(access_token="tok")
        result = c.delete_api_key(1)
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_delete_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("boom")
        c = CookieApiClient(access_token="tok")
        result = c.delete_api_key(1)
        assert result.success is False


class TestCookieApiRefreshApiKey:
    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_refresh_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"status": "active"})
        c = CookieApiClient(access_token="tok")
        result = c.refresh_api_key(42)
        assert result.success is True

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_refresh_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(500, "error")
        c = CookieApiClient(access_token="tok")
        result = c.refresh_api_key(42)
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_refresh_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        c = CookieApiClient(access_token="tok")
        result = c.refresh_api_key(42)
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_refresh_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("boom")
        c = CookieApiClient(access_token="tok")
        result = c.refresh_api_key(42)
        assert result.success is False


class TestCookieApiAssignApiKey:
    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_assign_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"id": 1, "flow_id": 5})
        c = CookieApiClient(access_token="tok")
        result = c.assign_api_key_to_flow(1, 5)
        assert result.success is True

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_assign_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(400, {"message": "Invalid"})
        c = CookieApiClient(access_token="tok")
        result = c.assign_api_key_to_flow(1, 5)
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_assign_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("refused")
        c = CookieApiClient(access_token="tok")
        result = c.assign_api_key_to_flow(1, 5)
        assert result.success is False

    @patch("app.api.cookie_api.urllib.request.urlopen")
    def test_assign_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("x")
        c = CookieApiClient(access_token="tok")
        result = c.assign_api_key_to_flow(1, 5)
        assert result.success is False


class TestCookieApiHandleHttpError:
    def test_json_error_body(self):
        c = CookieApiClient()
        err = _make_http_error(422, {"message": "Validation error"})
        result = c._handle_http_error(err, "test")
        assert "Validation error" in result.message

    def test_non_json_error_body(self):
        c = CookieApiClient()
        err = _make_http_error(500, "Internal Server Error")
        result = c._handle_http_error(err, "test")
        assert "500" in result.message
