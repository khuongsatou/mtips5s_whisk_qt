"""
Tests for WorkflowApiClient — workflow creation, linking, and image generation with mocked HTTP.
"""
import json
import time
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from app.api.workflow_api import WorkflowApiClient, ASPECT_RATIO_MAP


def _mock_response(body: dict, status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_http_error(code: int, body: str = ""):
    import urllib.error
    return urllib.error.HTTPError(
        url="http://test", code=code, msg="Error",
        hdrs={}, fp=BytesIO(body.encode("utf-8")),
    )


class TestWorkflowApiInit:
    def test_default_token(self):
        c = WorkflowApiClient()
        assert c._access_token == ""

    def test_set_access_token(self):
        c = WorkflowApiClient()
        c.set_access_token("tok")
        assert c._access_token == "tok"


class TestAspectRatioMap:
    def test_all_ratios_present(self):
        for ratio in ["VIDEO_ASPECT_RATIO_LANDSCAPE", "VIDEO_ASPECT_RATIO_PORTRAIT", "16:9", "9:16"]:
            assert ratio in ASPECT_RATIO_MAP

    def test_landscape(self):
        assert ASPECT_RATIO_MAP["VIDEO_ASPECT_RATIO_LANDSCAPE"] == "VIDEO_ASPECT_RATIO_LANDSCAPE"
        assert ASPECT_RATIO_MAP["16:9"] == "VIDEO_ASPECT_RATIO_LANDSCAPE"

    def test_portrait(self):
        assert ASPECT_RATIO_MAP["VIDEO_ASPECT_RATIO_PORTRAIT"] == "VIDEO_ASPECT_RATIO_PORTRAIT"
        assert ASPECT_RATIO_MAP["9:16"] == "VIDEO_ASPECT_RATIO_PORTRAIT"


class TestCreateWorkflow:
    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        resp_body = {
            "result": {"data": {"json": {"result": {
                "projectId": "wf-123",
                "projectInfo": {"projectTitle": "Feb 18 - 14:20"}
            }}}}
        }
        mock_urlopen.return_value = _mock_response(resp_body)
        c = WorkflowApiClient()
        result = c.create_workflow("session-tok")
        assert result.success is True
        assert result.data["workflowId"] == "wf-123"

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_with_csrf_token(self, mock_urlopen):
        resp_body = {
            "result": {"data": {"json": {"result": {
                "projectId": "wf-456",
                "projectInfo": {"projectTitle": "Feb 18 - 14:20"}
            }}}}
        }
        mock_urlopen.return_value = _mock_response(resp_body)
        c = WorkflowApiClient()
        result = c.create_workflow("session-tok", csrf_token="csrf-tok")
        assert result.success is True

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_no_workflow_id(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"result": {}})
        c = WorkflowApiClient()
        result = c.create_workflow("tok")
        assert result.success is False
        assert "No projectId" in result.message

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(403, "Forbidden")
        c = WorkflowApiClient()
        result = c.create_workflow("tok")
        assert result.success is False
        assert "403" in result.message

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("refused")
        c = WorkflowApiClient()
        result = c.create_workflow("tok")
        assert result.success is False
        assert "Cannot connect" in result.message

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("boom")
        c = WorkflowApiClient()
        result = c.create_workflow("tok")
        assert result.success is False


class TestLinkWorkflow:
    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"status": "ok"})
        c = WorkflowApiClient(access_token="tok")
        result = c.link_workflow(flow_id=1, project_id="wf-1", project_name="Test")
        assert result.success is True

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_not_ok_status(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"status": "fail"})
        c = WorkflowApiClient(access_token="tok")
        result = c.link_workflow(1, "wf-1", "Test")
        assert result.success is False

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(500, "Server Error")
        c = WorkflowApiClient(access_token="tok")
        result = c.link_workflow(1, "wf-1", "Test")
        assert result.success is False

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        c = WorkflowApiClient(access_token="tok")
        result = c.link_workflow(1, "wf-1", "Test")
        assert result.success is False

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("x")
        c = WorkflowApiClient(access_token="tok")
        result = c.link_workflow(1, "wf-1", "Test")
        assert result.success is False


class TestGenerateImage:
    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        body = {
            "responses": [{"videoId": "vid-1"}],
        }
        mock_urlopen.return_value = _mock_response(body)
        c = WorkflowApiClient()

        result = c.generate_image("gtoken", "wf-1", "test prompt")

        assert result.success is True
        assert result.data["response"] == body
        assert result.data["prompt"] == "test prompt"
        assert result.data["workflow_id"] == "wf-1"

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_custom_aspect_ratio(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"responses": []})
        c = WorkflowApiClient()
        c.generate_image("gtoken", "wf-1", "test", aspect_ratio="9:16")

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["requests"][0]["aspectRatio"] == "VIDEO_ASPECT_RATIO_PORTRAIT"

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_custom_seed(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"responses": []})
        c = WorkflowApiClient()
        c.generate_image("gtoken", "wf-1", "test", seed=99999)

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["requests"][0]["seed"] == 99999

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_unknown_aspect_ratio_fallback(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"responses": []})
        c = WorkflowApiClient()
        c.generate_image("gtoken", "wf-1", "test", aspect_ratio="99:1")

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["requests"][0]["aspectRatio"] == "VIDEO_ASPECT_RATIO_LANDSCAPE"

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(429, "Rate limited")
        c = WorkflowApiClient()
        result = c.generate_image("gtoken", "wf-1", "test")
        assert result.success is False
        assert "429" in result.message

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        c = WorkflowApiClient()
        result = c.generate_image("gtoken", "wf-1", "test")
        assert result.success is False

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("crash")
        c = WorkflowApiClient()
        result = c.generate_image("gtoken", "wf-1", "test")
        assert result.success is False
