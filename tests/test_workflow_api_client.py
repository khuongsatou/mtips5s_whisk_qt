"""
Tests for WorkflowApiClient — create_workflow, link_workflow,
upload/caption reference images, and generate_image.

All HTTP calls are mocked via urllib.request.urlopen patching.
"""
import io
import json
import os
import base64
import tempfile
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import urllib.error

from app.api.workflow_api.workflow_api import WorkflowApiClient
from app.api.workflow_api.constants import ASPECT_RATIO_MAP


# ── Helpers ────────────────────────────────────────────────────────

def _mock_response(data: dict, status: int = 200):
    """Create a mock HTTP response that behaves like urlopen context manager."""
    body = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = body
    resp.status = status
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ── Constructor ────────────────────────────────────────────────────


class TestConstructor:
    def test_default_token_empty(self):
        client = WorkflowApiClient()
        assert client._access_token == ""

    def test_set_access_token(self):
        client = WorkflowApiClient()
        client.set_access_token("test123")
        assert client._access_token == "test123"

    def test_init_with_token(self):
        client = WorkflowApiClient(access_token="init_token")
        assert client._access_token == "init_token"


# ── Create Workflow ────────────────────────────────────────────────


class TestCreateWorkflow:
    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        resp_data = {
            "result": {"data": {"json": {"result": {
                "projectId": "wf-abc-123",
                "projectInfo": {"projectTitle": "Feb 18 - 14:20"}
            }}}}
        }
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient()
        result = client.create_workflow(session_token="session123")
        assert result.success is True
        assert result.data["workflowId"] == "wf-abc-123"
        assert "workflowName" in result.data

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_no_workflow_id(self, mock_urlopen):
        resp_data = {"result": {"data": {"json": {"result": {}}}}}
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient()
        result = client.create_workflow(session_token="session123")
        assert result.success is False

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        error_resp = MagicMock()
        error_resp.read.return_value = b"Unauthorized"
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=401, msg="", hdrs={}, fp=error_resp
        )

        client = WorkflowApiClient()
        result = client.create_workflow(session_token="bad")
        assert result.success is False
        assert "401" in result.message

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_url_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        client = WorkflowApiClient()
        result = client.create_workflow(session_token="test")
        assert result.success is False
        assert "Cannot connect" in result.message

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Unexpected error")

        client = WorkflowApiClient()
        result = client.create_workflow(session_token="test")
        assert result.success is False

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_with_csrf_token(self, mock_urlopen):
        resp_data = {
            "result": {"data": {"json": {"result": {
                "projectId": "wf-123",
                "projectInfo": {"projectTitle": "Feb 18 - 14:20"}
            }}}}
        }
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient()
        result = client.create_workflow(
            session_token="sess", csrf_token="csrf123"
        )
        assert result.success is True
        # Verify CSRF token in cookie header
        call_args = mock_urlopen.call_args[0][0]
        assert "csrf" in call_args.get_header("Cookie").lower()


# ── Link Workflow ──────────────────────────────────────────────────


class TestLinkWorkflow:
    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        resp_data = {"status": "ok", "message": "Linked"}
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient(access_token="token123")
        result = client.link_workflow(
            flow_id=1, project_id="wf-123", project_name="My Project"
        )
        assert result.success is True

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_not_ok_status(self, mock_urlopen):
        resp_data = {"status": "error", "message": "Flow not found"}
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient(access_token="token123")
        result = client.link_workflow(
            flow_id=1, project_id="wf-123", project_name="Test"
        )
        assert result.success is False

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        error_resp = MagicMock()
        error_resp.read.return_value = b"Server Error"
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=500, msg="", hdrs={}, fp=error_resp
        )

        client = WorkflowApiClient(access_token="token")
        result = client.link_workflow(
            flow_id=1, project_id="wf-123", project_name="Test"
        )
        assert result.success is False
        assert "500" in result.message

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_url_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Timeout")

        client = WorkflowApiClient(access_token="token")
        result = client.link_workflow(
            flow_id=1, project_id="wf-123", project_name="Test"
        )
        assert result.success is False


# ── Caption Image ──────────────────────────────────────────────────


class TestCaptionImage:
    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        resp_data = {
            "result": {"data": {"json": {"result": {
                "candidates": [{"output": "A beautiful sunset"}]
            }}}}
        }
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient()
        result = client.caption_image(
            session_token="sess", image_base64="data:image/png;base64,..."
        )
        assert result.success is True
        assert result.data["caption"] == "A beautiful sunset"

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_no_candidates(self, mock_urlopen):
        resp_data = {"result": {"data": {"json": {"result": {"candidates": []}}}}}
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient()
        result = client.caption_image(session_token="sess", image_base64="data:...")
        assert result.success is False

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        error_resp = MagicMock()
        error_resp.read.return_value = b"Bad Request"
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=400, msg="", hdrs={}, fp=error_resp
        )

        client = WorkflowApiClient()
        result = client.caption_image(session_token="sess", image_base64="data:...")
        assert result.success is False


# ── Upload Image ───────────────────────────────────────────────────


class TestUploadImage:
    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        resp_data = {
            "result": {"data": {"json": {"result": {
                "uploadMediaGenerationId": "upload-xyz-789"
            }}}}
        }
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient()
        result = client.upload_image(
            session_token="sess", image_base64="data:image/png;base64,..."
        )
        assert result.success is True
        assert result.data["uploadMediaGenerationId"] == "upload-xyz-789"

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_no_upload_id(self, mock_urlopen):
        resp_data = {"result": {"data": {"json": {"result": {}}}}}
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient()
        result = client.upload_image(session_token="sess", image_base64="data:...")
        assert result.success is False


# ── Upload Reference Image ────────────────────────────────────────


class TestUploadReferenceImage:
    def test_read_file_error(self):
        client = WorkflowApiClient()
        result = client.upload_reference_image(
            session_token="sess",
            image_path="/nonexistent/file.png",
            category="title",
        )
        assert result.success is False
        assert "Cannot read" in result.message

    @patch.object(WorkflowApiClient, "upload_image")
    @patch.object(WorkflowApiClient, "caption_image")
    def test_success(self, mock_caption, mock_upload, tmp_path):
        # Create temp image
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"\x89PNG\r\n\x1a\n")

        mock_caption.return_value = MagicMock(
            success=True, data={"caption": "A test image"}
        )
        mock_upload.return_value = MagicMock(
            success=True, data={"uploadMediaGenerationId": "upload-123"}
        )

        client = WorkflowApiClient()
        result = client.upload_reference_image(
            session_token="sess",
            image_path=str(img_path),
            category="title",
        )
        assert result.success is True
        assert result.data["uploadMediaGenerationId"] == "upload-123"
        assert result.data["caption"] == "A test image"
        assert result.data["mediaCategory"] == "MEDIA_CATEGORY_SUBJECT"

    @patch.object(WorkflowApiClient, "upload_image")
    @patch.object(WorkflowApiClient, "caption_image")
    def test_upload_fails(self, mock_caption, mock_upload, tmp_path):
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"\xff\xd8\xff\xe0")

        mock_caption.return_value = MagicMock(success=True, data={"caption": "x"})
        mock_upload.return_value = MagicMock(success=False, message="Upload failed")

        client = WorkflowApiClient()
        result = client.upload_reference_image(
            session_token="sess",
            image_path=str(img_path),
            category="scene",
        )
        assert result.success is False

    @patch.object(WorkflowApiClient, "upload_image")
    @patch.object(WorkflowApiClient, "caption_image")
    def test_caption_fails_upload_succeeds(self, mock_caption, mock_upload, tmp_path):
        img_path = tmp_path / "test.webp"
        img_path.write_bytes(b"RIFF\x00\x00\x00\x00WEBP")

        mock_caption.return_value = MagicMock(success=False, data={})
        mock_upload.return_value = MagicMock(
            success=True, data={"uploadMediaGenerationId": "up-456"}
        )

        client = WorkflowApiClient()
        result = client.upload_reference_image(
            session_token="sess",
            image_path=str(img_path),
            category="style",
        )
        assert result.success is True
        assert result.data["caption"] == ""  # Caption failed gracefully

    @patch.object(WorkflowApiClient, "upload_image")
    @patch.object(WorkflowApiClient, "caption_image")
    def test_category_mapping(self, mock_caption, mock_upload, tmp_path):
        img_path = tmp_path / "test.gif"
        img_path.write_bytes(b"GIF89a")

        mock_caption.return_value = MagicMock(success=True, data={"caption": ""})
        mock_upload.return_value = MagicMock(
            success=True, data={"uploadMediaGenerationId": "up-789"}
        )

        client = WorkflowApiClient()

        for cat, expected in WorkflowApiClient.MEDIA_CATEGORY_MAP.items():
            result = client.upload_reference_image(
                session_token="sess",
                image_path=str(img_path),
                category=cat,
            )
            assert result.data["mediaCategory"] == expected


# ── Generate Image ─────────────────────────────────────────────────


class TestGenerateImage:
    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_success_without_media(self, mock_urlopen):
        resp_data = {"responses": [{"videoId": "vid-1"}]}
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient()
        result = client.generate_image(
            google_access_token="ya29.test",
            workflow_id="wf-123",
            prompt="A beautiful sunset",
        )
        assert result.success is True
        assert "response" in result.data
        assert "workflow_id" in result.data

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_success_with_media_inputs(self, mock_urlopen):
        resp_data = {"responses": [{"videoId": "vid-2"}]}
        mock_urlopen.return_value = _mock_response(resp_data)

        media = [
            {"uploadMediaGenerationId": "up-1", "mediaCategory": "MEDIA_CATEGORY_SUBJECT"}
        ]
        client = WorkflowApiClient()
        result = client.generate_image(
            google_access_token="ya29.test",
            workflow_id="wf-123",
            prompt="Test",
            media_inputs=media,
        )
        assert result.success is True

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        error_resp = MagicMock()
        error_resp.read.return_value = b"Rate limited"
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=429, msg="", hdrs={}, fp=error_resp
        )

        client = WorkflowApiClient()
        result = client.generate_image(
            google_access_token="ya29.test",
            workflow_id="wf-123",
            prompt="Test",
        )
        assert result.success is False
        assert "429" in result.message

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_timeout_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("timed out")

        client = WorkflowApiClient()
        result = client.generate_image(
            google_access_token="ya29.test",
            workflow_id="wf-123",
            prompt="Test",
        )
        assert result.success is False

    @patch("app.api.workflow_api.workflow_api.urllib.request.urlopen")
    def test_custom_timeout(self, mock_urlopen):
        resp_data = {"responses": [{"videoId": "vid-3"}]}
        mock_urlopen.return_value = _mock_response(resp_data)

        client = WorkflowApiClient()
        client.generate_image(
            google_access_token="ya29.test",
            workflow_id="wf-123",
            prompt="Test",
            timeout=30,
        )
        # Verify timeout was passed to urlopen
        call_kwargs = mock_urlopen.call_args
        assert call_kwargs[1].get("timeout") == 30 or call_kwargs.kwargs.get("timeout") == 30


# ── Constants ──────────────────────────────────────────────────────


class TestConstants:
    def test_aspect_ratio_map_has_standard_ratios(self):
        assert "VIDEO_ASPECT_RATIO_LANDSCAPE" in ASPECT_RATIO_MAP
        assert "VIDEO_ASPECT_RATIO_PORTRAIT" in ASPECT_RATIO_MAP
        assert "16:9" in ASPECT_RATIO_MAP
        assert "9:16" in ASPECT_RATIO_MAP

    def test_media_category_map(self):
        assert WorkflowApiClient.MEDIA_CATEGORY_MAP["title"] == "MEDIA_CATEGORY_SUBJECT"
        assert WorkflowApiClient.MEDIA_CATEGORY_MAP["scene"] == "MEDIA_CATEGORY_SCENE"
        assert WorkflowApiClient.MEDIA_CATEGORY_MAP["style"] == "MEDIA_CATEGORY_STYLE"
