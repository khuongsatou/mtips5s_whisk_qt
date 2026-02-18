"""
Tests for PageHandlersMixin — queue operations, task progress,
auto-retry, workflow persistence, download, and auth helpers.
"""
import os
import time
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer, QSettings
from PySide6.QtWidgets import QFileDialog
from app.api.models import ApiResponse


# ── Fake page that uses the mixin ──────────────────────────────────

def _make_page(mock_api=None, translator=None):
    """Create a minimal object that inherits from PageHandlersMixin."""
    from app.pages.image_creator_page.page_handlers import PageHandlersMixin

    class FakePage(PageHandlersMixin):
        pass

    page = FakePage()
    page.api = mock_api or MagicMock()
    page.cookie_api = MagicMock()
    page.translator = translator or MagicMock()
    page.translator.t = MagicMock(side_effect=lambda key: key)

    # Simulate required attributes that ImageCreatorPage normally provides
    page._selected_ids = []
    page._is_generating = False
    page._worker = None
    page._running_task_ids = set()
    page._local_progress = {}
    page._task_start_times = {}
    page._upload_status = {}
    page._retry_counts = {}
    page._active_flow_id = 0
    page._workflow_id = ""
    page._workflow_name = ""
    page.MAX_RETRIES = 3

    page._table = MagicMock()
    page._config = MagicMock()
    page._toast = MagicMock()
    page._progress_timer = MagicMock()
    page._auto_retry_timer = MagicMock()
    page.refresh_data = MagicMock()

    return page


# ── Queue Operations ──────────────────────────────────────────────


class TestPromptEdited:
    def test_updates_task_via_api(self):
        page = _make_page()
        page._on_prompt_edited("task-1", "hello world")
        page.api.update_task.assert_called_once_with("task-1", {"prompt": "hello world"})

    def test_normalizes_prompt(self):
        page = _make_page()
        page._on_prompt_edited("task-1", "  hello  \n  world  ")
        call_args = page.api.update_task.call_args[0]
        assert call_args[0] == "task-1"
        # Normalized prompt
        assert call_args[1]["prompt"].strip() != ""


class TestSelectionChanged:
    def test_stores_selected_ids(self):
        page = _make_page()
        page._on_selection_changed(["a", "b", "c"])
        assert page._selected_ids == ["a", "b", "c"]

    def test_empty_selection(self):
        page = _make_page()
        page._on_selection_changed([])
        assert page._selected_ids == []


class TestAddToQueue:
    def test_adds_single_prompt(self):
        page = _make_page()

        config = {
            "prompt": "A cat on a table",
            "model": "veo_3_1_t2v_fast_ultra_relaxed",
            "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
            "quality": "1K",
            "images_per_prompt": 1,
        }
        page._on_add_to_queue(config)
        page.api.add_to_queue.assert_called_once()
        page.refresh_data.assert_called_once()

    def test_splits_multi_line_prompts(self):
        page = _make_page()

        config = {
            "prompt": "cat\ndog\nbird",
            "model": "veo_3_1_t2v_fast_ultra_relaxed",
        }
        page._on_add_to_queue(config)
        assert page.api.add_to_queue.call_count == 3

    def test_ignores_empty_prompt(self):
        page = _make_page()
        page._on_add_to_queue({"prompt": ""})
        page.api.add_to_queue.assert_not_called()

    def test_ignores_whitespace_only(self):
        page = _make_page()
        page._on_add_to_queue({"prompt": "   \n  \n  "})
        page.api.add_to_queue.assert_not_called()

    def test_max_300_prompts_rejected(self):
        page = _make_page()
        prompts = "\n".join(f"prompt {i}" for i in range(301))
        config = {"prompt": prompts}

        with patch("app.pages.image_creator_page.page_handlers.StyledMessageBox") as mock_box:
            page._on_add_to_queue(config)
            mock_box.warning.assert_called_once()
            page.api.add_to_queue.assert_not_called()

    def test_exactly_300_prompts_accepted(self):
        page = _make_page()
        prompts = "\n".join(f"prompt {i}" for i in range(300))
        config = {"prompt": prompts}
        page._on_add_to_queue(config)
        assert page.api.add_to_queue.call_count == 300

    def test_reference_images_by_cat_stored(self):
        page = _make_page()
        config = {
            "prompt": "test prompt",
            "ref_title_images": ["/img/t1.png"],
            "ref_scene_images": ["/img/s1.png"],
            "ref_style_images": [],
        }
        page._on_add_to_queue(config)

        call_data = page.api.add_to_queue.call_args[0][0]
        assert call_data["reference_images_by_cat"]["title"] == ["/img/t1.png"]
        assert call_data["reference_images_by_cat"]["scene"] == ["/img/s1.png"]
        assert call_data["reference_images_by_cat"]["style"] == []

    def test_json_prompt_kept_as_single(self):
        page = _make_page()
        json_prompt = '{"prompt": "a cat", "neg": "blurry"}'
        config = {"prompt": json_prompt}
        page._on_add_to_queue(config)
        assert page.api.add_to_queue.call_count == 1

    def test_preloaded_media_inputs_passed(self):
        page = _make_page()
        media = [{"type": "image", "id": "abc"}]
        config = {
            "prompt": "test",
            "preloaded_media_inputs": media,
        }
        page._on_add_to_queue(config)
        call_data = page.api.add_to_queue.call_args[0][0]
        assert call_data["preloaded_media_inputs"] == media


class TestAddRow:
    def test_adds_empty_task(self):
        page = _make_page()
        page._on_add_row()
        page.api.add_to_queue.assert_called_once()
        call_data = page.api.add_to_queue.call_args[0][0]
        assert call_data["prompt"] == ""
        page.refresh_data.assert_called_once()


class TestDeleteSelected:
    def test_deletes_selected(self):
        page = _make_page()
        page._selected_ids = ["a", "b"]
        page._on_delete_selected()
        # After call, the list is cleared, but delete_tasks was called with the IDs
        page.api.delete_tasks.assert_called_once()
        # The list was cleared after the call
        assert page._selected_ids == []
        page.refresh_data.assert_called_once()

    def test_no_selection_no_call(self):
        page = _make_page()
        page._selected_ids = []
        page._on_delete_selected()
        page.api.delete_tasks.assert_not_called()


class TestDeleteAll:
    def test_clears_queue_on_confirm(self):
        page = _make_page()
        with patch("app.pages.image_creator_page.page_handlers.StyledMessageBox") as mock_box:
            mock_box.question.return_value = True
            page._on_delete_all()
            page.api.clear_queue.assert_called_once()

    def test_does_not_clear_on_cancel(self):
        page = _make_page()
        with patch("app.pages.image_creator_page.page_handlers.StyledMessageBox") as mock_box:
            mock_box.question.return_value = False
            page._on_delete_all()
            page.api.clear_queue.assert_not_called()


class TestRetryErrors:
    def test_resets_counts_and_retries(self):
        page = _make_page()
        page._retry_counts = {"t1": 2, "t2": 1}
        page._on_retry_errors()
        assert page._retry_counts == {}
        page._auto_retry_timer.stop.assert_called()
        page.api.retry_errors.assert_called_once()
        page.refresh_data.assert_called()


class TestClearCheckpoint:
    def test_clears_on_confirm(self):
        page = _make_page()
        with patch("app.pages.image_creator_page.page_handlers.StyledMessageBox") as mock_box:
            mock_box.question.return_value = True
            page._on_clear_checkpoint()
            page.api.clear_checkpoint.assert_called_once()

    def test_does_not_clear_on_cancel(self):
        page = _make_page()
        with patch("app.pages.image_creator_page.page_handlers.StyledMessageBox") as mock_box:
            mock_box.question.return_value = False
            page._on_clear_checkpoint()
            page.api.clear_checkpoint.assert_not_called()


# ── Task Progress ──────────────────────────────────────────────────


class TestOnTaskProgress:
    def test_running_status_tracked(self):
        page = _make_page()
        page._on_task_progress("t1", 50, "running", {})
        assert "t1" in page._running_task_ids
        assert page._local_progress["t1"] == 50

    def test_running_records_start_time(self):
        page = _make_page()
        page._on_task_progress("t1", 10, "running", {})
        assert "t1" in page._task_start_times

    def test_completed_cleans_up(self):
        page = _make_page()
        page._running_task_ids.add("t1")
        page._local_progress["t1"] = 80
        page._task_start_times["t1"] = time.time()
        page._on_task_progress("t1", 100, "completed", {})
        assert "t1" not in page._running_task_ids
        assert "t1" not in page._local_progress
        assert "t1" not in page._task_start_times
        page.refresh_data.assert_called()

    def test_error_increments_retry_count(self):
        page = _make_page()
        page._on_task_progress("t1", 0, "error", {"error_message": "fail"})
        assert page._retry_counts["t1"] == 1
        page._on_task_progress("t1", 0, "error", {"error_message": "fail again"})
        assert page._retry_counts["t1"] == 2

    def test_completed_adds_timestamp(self):
        page = _make_page()
        page._on_task_progress("t1", 100, "completed", {})
        call_data = page.api.update_task.call_args[0][1]
        assert "completed_at" in call_data

    def test_running_starts_timer(self):
        page = _make_page()
        page._progress_timer.isActive.return_value = False
        page._on_task_progress("t1", 10, "running", {})
        page._progress_timer.start.assert_called()

    def test_upload_status_tracked(self):
        page = _make_page()
        page._on_task_progress("t1", 10, "running", {"upload_status": "Uploading..."})
        assert page._upload_status["t1"] == "Uploading..."

    def test_upload_status_cleared_on_empty(self):
        page = _make_page()
        page._upload_status["t1"] = "Uploading..."
        page._on_task_progress("t1", 50, "running", {"upload_status": ""})
        assert "t1" not in page._upload_status


class TestTickProgress:
    def test_stops_timer_when_no_running(self):
        page = _make_page()
        page._running_task_ids = set()
        page._tick_progress()
        page._progress_timer.stop.assert_called()

    def test_increments_progress(self):
        page = _make_page()
        page._running_task_ids = {"t1"}
        page._local_progress = {"t1": 50}
        page._task_start_times = {"t1": time.time()}
        page._tick_progress()
        assert page._local_progress["t1"] > 50
        assert page._local_progress["t1"] <= 99

    def test_caps_at_99(self):
        page = _make_page()
        page._running_task_ids = {"t1"}
        page._local_progress = {"t1": 98}
        page._task_start_times = {"t1": time.time()}
        page._tick_progress()
        assert page._local_progress["t1"] <= 99


class TestOnWorkerFinished:
    def test_resets_all_state(self):
        page = _make_page()
        page._is_generating = True
        page._worker = MagicMock()
        page._running_task_ids = {"t1", "t2"}
        page._local_progress = {"t1": 50}
        page._task_start_times = {"t1": time.time()}
        page._upload_status = {"t1": "test"}
        page._config.is_auto_retry_enabled = False

        page._on_worker_finished()

        assert page._is_generating is False
        assert page._worker is None
        assert len(page._running_task_ids) == 0
        assert len(page._local_progress) == 0
        assert len(page._task_start_times) == 0
        page._progress_timer.stop.assert_called()
        page.refresh_data.assert_called()


class TestShowCompletionToast:
    def test_shows_success_toast(self):
        page = _make_page()
        page.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[
                {"status": "completed"},
                {"status": "completed"},
            ],
        )
        page._show_completion_toast()
        page._toast.show_message.assert_called_once()
        call_args = page._toast.show_message.call_args
        assert "2" in call_args[0][0]
        assert call_args[1].get("icon") == "✅"

    def test_shows_warning_toast_with_errors(self):
        page = _make_page()
        page.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[
                {"status": "completed"},
                {"status": "error"},
            ],
        )
        page._show_completion_toast()
        call_args = page._toast.show_message.call_args
        assert call_args[1].get("icon") == "⚠️"


# ── Auto-Retry ─────────────────────────────────────────────────────


class TestScheduleAutoRetry:
    def test_schedules_when_retryable_tasks_exist(self):
        page = _make_page()
        page.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[{"id": "t1", "status": "error"}],
        )
        page._retry_counts = {}
        page._schedule_auto_retry()
        page._auto_retry_timer.start.assert_called()

    def test_skips_when_max_retries_exceeded(self):
        page = _make_page()
        page.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[{"id": "t1", "status": "error"}],
        )
        page._retry_counts = {"t1": 10}
        page._schedule_auto_retry()
        page._auto_retry_timer.start.assert_not_called()

    def test_skips_when_no_data(self):
        page = _make_page()
        page.api.get_queue.return_value = ApiResponse(
            success=True, data=None,
        )
        page._schedule_auto_retry()
        page._auto_retry_timer.start.assert_not_called()


class TestDoAutoRetry:
    def test_skips_when_generating(self):
        page = _make_page()
        page._is_generating = True
        page._do_auto_retry()
        page.api.get_queue.assert_not_called()

    def test_skips_when_toggle_disabled(self):
        page = _make_page()
        page._config.is_auto_retry_enabled = False
        page._do_auto_retry()
        page.api.get_queue.assert_not_called()

    def test_resets_retryable_tasks_to_pending(self):
        page = _make_page()
        page._config.is_auto_retry_enabled = True
        page.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[
                {"id": "t1", "status": "error"},
                {"id": "t2", "status": "completed"},
            ],
        )
        page._retry_counts = {"t1": 1}

        with patch.object(page, '_run_tasks'):
            page._do_auto_retry()

        # Only t1 should be reset
        page.api.update_task.assert_called_once()
        update_data = page.api.update_task.call_args[0][1]
        assert update_data["status"] == "pending"


# ── Auth Helpers ───────────────────────────────────────────────────


class TestGetGoogleAccessToken:
    def test_returns_token_on_success(self):
        page = _make_page()
        page.cookie_api.get_api_keys.return_value = ApiResponse(
            success=True,
            data={
                "items": [{
                    "value": "ya29.test_token",
                    "metadata": {
                        "cookies": {
                            "__Secure-next-auth.session-token": "session123",
                        }
                    },
                }]
            },
        )
        token, wf_id, session, error = page._get_google_access_token()
        assert token == "ya29.test_token"
        assert session == "session123"
        assert error is None

    def test_returns_error_when_no_cookies(self):
        page = _make_page()
        page.cookie_api.get_api_keys.return_value = ApiResponse(
            success=True, data={"items": []},
        )
        _, _, _, error = page._get_google_access_token()
        assert error is not None

    def test_returns_error_when_api_fails(self):
        page = _make_page()
        page.cookie_api.get_api_keys.return_value = ApiResponse(
            success=False, data=None,
        )
        _, _, _, error = page._get_google_access_token()
        assert error is not None

    def test_returns_error_when_no_access_token(self):
        page = _make_page()
        page.cookie_api.get_api_keys.return_value = ApiResponse(
            success=True,
            data={"items": [{"value": "", "metadata": {}}]},
        )
        _, _, _, error = page._get_google_access_token()
        assert error is not None

    def test_handles_exception(self):
        page = _make_page()
        page.cookie_api.get_api_keys.side_effect = Exception("Network error")
        _, _, _, error = page._get_google_access_token()
        assert error is not None
        assert "Network error" in error


# ── Workflow Persistence ───────────────────────────────────────────


class TestWorkflowPersistence:
    def test_save_and_load(self):
        page = _make_page()
        page._save_workflow(42, "wf-abc-123", "My Project")
        page._load_workflow(42)
        assert page._workflow_id == "wf-abc-123"
        assert page._workflow_name == "My Project"

    def test_load_nonexistent_returns_empty(self):
        page = _make_page()
        page._load_workflow(999999)
        assert page._workflow_id == ""
        assert page._workflow_name == ""

    def test_load_updates_config_panel(self):
        page = _make_page()
        page._save_workflow(99, "wf-xyz", "Test Proj")
        page._load_workflow(99)
        page._config.set_workflow_status.assert_called()


# ── Download ───────────────────────────────────────────────────────


class TestDownload:
    def test_download_copies_files(self, tmp_path):
        page = _make_page()
        # Create fake output image
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        img_file = src_dir / "001.png"
        img_file.write_bytes(b"fake png data")

        page.api.get_task.return_value = ApiResponse(
            success=True,
            data={
                "id": "t1",
                "status": "completed",
                "output_images": [str(img_file)],
                "stt": 1,
            },
        )

        dst_dir = tmp_path / "dst"
        dst_dir.mkdir()
        with patch("app.pages.image_creator_page.page_handlers.QFileDialog") as mock_fd:
            mock_fd.getExistingDirectory.return_value = str(dst_dir)
            page._on_download("t1")

        # Check file was copied
        copied = list(dst_dir.iterdir())
        assert len(copied) == 1

    def test_download_skips_missing_files(self, tmp_path):
        page = _make_page()
        page.api.get_task.return_value = ApiResponse(
            success=True,
            data={
                "id": "t1",
                "status": "completed",
                "output_images": ["/nonexistent/path.png"],
                "stt": 1,
            },
        )

        with patch("app.pages.image_creator_page.page_handlers.QFileDialog") as mock_fd:
            mock_fd.getExistingDirectory.return_value = str(tmp_path)
            page._on_download("t1")  # Should not crash

    def test_download_cancelled(self):
        page = _make_page()
        page.api.get_task.return_value = ApiResponse(
            success=True,
            data={
                "id": "t1",
                "status": "completed",
                "output_images": ["/some/image.png"],
                "stt": 1,
            },
        )

        with patch("app.pages.image_creator_page.page_handlers.QFileDialog") as mock_fd:
            mock_fd.getExistingDirectory.return_value = ""
            page._on_download("t1")  # Should not crash

    def test_download_no_images_shows_info(self):
        page = _make_page()
        page.api.get_task.return_value = ApiResponse(
            success=True,
            data={"id": "t1", "status": "completed", "output_images": []},
        )
        with patch("app.pages.image_creator_page.page_handlers.StyledMessageBox") as mock_box:
            page._on_download("t1")
            mock_box.information.assert_called_once()


class TestDownloadAll:
    def test_download_all_copies_completed(self, tmp_path):
        page = _make_page()
        # Create fake output images
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        img1 = src_dir / "001.png"
        img1.write_bytes(b"data1")
        img2 = src_dir / "002.png"
        img2.write_bytes(b"data2")

        page.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[
                {"id": "t1", "stt": 1, "status": "completed", "output_images": [str(img1)]},
                {"id": "t2", "stt": 2, "status": "completed", "output_images": [str(img2)]},
                {"id": "t3", "stt": 3, "status": "error", "output_images": []},
            ],
        )

        dst_dir = tmp_path / "dst"
        dst_dir.mkdir()
        with patch("app.pages.image_creator_page.page_handlers.QFileDialog") as mock_fd:
            mock_fd.getExistingDirectory.return_value = str(dst_dir)
            page._on_download_all()

        copied = list(dst_dir.iterdir())
        assert len(copied) == 2

    def test_download_all_cancelled(self):
        page = _make_page()
        page.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[{"id": "t1", "status": "completed", "output_images": ["/x.png"]}],
        )
        with patch("app.pages.image_creator_page.page_handlers.QFileDialog") as mock_fd:
            mock_fd.getExistingDirectory.return_value = ""
            page._on_download_all()  # Should not crash

    def test_download_all_no_completed(self):
        page = _make_page()
        page.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[{"id": "t1", "status": "error", "output_images": []}],
        )

        with patch("app.pages.image_creator_page.page_handlers.StyledMessageBox") as mock_box:
            page._on_download_all()
            mock_box.information.assert_called()


# ── Retranslate ────────────────────────────────────────────────────


class TestRetranslate:
    def test_calls_refresh_data(self):
        page = _make_page()
        page.retranslate()
        page.refresh_data.assert_called()
