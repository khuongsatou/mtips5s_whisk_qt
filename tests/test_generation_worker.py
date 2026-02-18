"""
Tests for GenerationWorker — batch video generation, polling, progress, concurrency.
"""
import os
import time
import base64
import tempfile
import pytest
from unittest.mock import MagicMock, patch

# Force headless Qt
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.pages.image_creator_page import GenerationWorker
from app.api.models import ApiResponse


def _make_task(task_id="t1", stt=1, prompt="test prompt", **overrides):
    """Helper to create a task dict."""
    task = {
        "id": task_id,
        "stt": stt,
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "images_per_prompt": 1,
        "output_folder": "",
        "filename_prefix": "",
    }
    task.update(overrides)
    return task


def _make_api_response(success=True, operation_name="op-test-123", scene_id="scene-test-456"):
    """Helper to create a mock generate_image API response (async format)."""
    if success:
        return ApiResponse(
            success=True,
            data={
                "response": {
                    "operations": [
                        {
                            "operation": {"name": operation_name},
                            "sceneId": scene_id,
                            "status": "MEDIA_GENERATION_STATUS_ACTIVE",
                        }
                    ]
                },
                "seed": 12345,
                "scene_id": scene_id,
                "workflow_id": "wf-test",
                "prompt": "test prompt",
            },
            message="Video generation started",
        )
    return ApiResponse(success=False, data={}, message="API Error: test failure")


def _make_status_response(status="MEDIA_GENERATION_STATUS_SUCCESSFUL", fife_url="https://example.com/video.mp4"):
    """Helper to create a mock check_video_status API response."""
    if status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
        return ApiResponse(
            success=True,
            data={
                "status": status,
                "fife_url": fife_url,
                "media_generation_id": "media-gen-id",
                "prompt": "test prompt",
                "seed": 12345,
                "remaining_credits": 100,
            },
            message="Video generation completed",
        )
    elif status == "MEDIA_GENERATION_STATUS_FAILED":
        return ApiResponse(
            success=False,
            data={"status": status},
            message="Video generation failed: test error",
        )
    else:
        return ApiResponse(
            success=True,
            data={"status": status},
            message=f"Status: {status}",
        )


def _make_mock_bridge():
    """Create a mock captcha bridge that immediately provides a token."""
    bridge = MagicMock()
    bridge.total_tokens_received = 1
    bridge._last_token = "MOCK_CAPTCHA_TOKEN"
    bridge.isRunning.return_value = True
    def _request_token(**kwargs):
        bridge.total_tokens_received += 1
        bridge._last_token = "MOCK_CAPTCHA_TOKEN"
    bridge.request_token.side_effect = _request_token
    return bridge


def _make_worker(tasks=None, **kwargs):
    """Helper to create a GenerationWorker with defaults."""
    defaults = {
        "workflow_api": MagicMock(),
        "google_token": "test_token",
        "workflow_id": "wf-test",
        "tasks": tasks or [],
        "concurrency": 2,
        "captcha_bridge": _make_mock_bridge(),
        "poll_interval": 1,
    }
    defaults.update(kwargs)
    return GenerationWorker(**defaults)


class TestGenerationWorkerInit:
    """Test worker initialization."""

    def test_init_stores_params(self):
        api = MagicMock()
        worker = _make_worker(
            workflow_api=api, google_token="tok", workflow_id="wf-1",
            tasks=[_make_task()], concurrency=3,
        )
        assert worker.workflow_api is api
        assert worker.google_token == "tok"
        assert worker.workflow_id == "wf-1"
        assert worker.concurrency == 3
        assert len(worker.tasks) == 1

    def test_concurrency_minimum_one(self):
        worker = _make_worker(concurrency=0)
        assert worker.concurrency == 1

    def test_default_concurrency(self):
        worker = _make_worker()
        assert worker.concurrency == 2

    def test_timeout_constant(self):
        worker = _make_worker()
        assert worker.TASK_TIMEOUT == 600

    def test_initial_stop_flag_false(self):
        worker = _make_worker()
        assert worker._stop_flag is False

    def test_stop_sets_flag(self):
        worker = _make_worker()
        worker.stop()
        assert worker._stop_flag is True

    def test_poll_interval_stored(self):
        worker = _make_worker(poll_interval=45)
        assert worker.poll_interval == 45

    def test_poll_interval_minimum_five(self):
        worker = _make_worker(poll_interval=2)
        assert worker.poll_interval == 5


class TestGenerationWorkerProcessTask:
    """Test _process_task logic."""

    @patch.object(GenerationWorker, '_download_video', return_value="/tmp/test.mp4")
    def test_successful_generate_emits_completed(self, mock_dl, tmp_path):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=True)
        api.check_video_status.return_value = _make_status_response()

        task = _make_task(output_folder=str(tmp_path))
        worker = _make_worker(workflow_api=api, tasks=[task])

        signals = []
        worker.task_progress.connect(lambda *args: signals.append(args))

        worker._process_task(task)

        assert len(signals) >= 2
        last = signals[-1]
        assert last[0] == "t1"
        assert last[1] == 100
        assert last[2] == "completed"

    def test_failed_generate_emits_error(self):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=False)

        task = _make_task()
        worker = _make_worker(workflow_api=api, tasks=[task])

        signals = []
        worker.task_progress.connect(lambda *args: signals.append(args))

        worker._process_task(task)

        last = signals[-1]
        assert last[0] == "t1"
        assert last[2] == "error"
        assert "error_message" in last[3]

    def test_initial_progress_between_10_and_15(self, tmp_path):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=True)
        api.check_video_status.return_value = _make_status_response()

        task = _make_task(output_folder=str(tmp_path))
        worker = _make_worker(workflow_api=api, tasks=[task])

        signals = []
        worker.task_progress.connect(lambda *args: signals.append(args))

        with patch.object(GenerationWorker, '_download_video', return_value="/tmp/t.mp4"):
            worker._process_task(task)

        first = signals[0]
        assert first[2] == "running"
        assert 10 <= first[1] <= 15

    def test_stop_flag_skips_task(self):
        api = MagicMock()
        task = _make_task()
        worker = _make_worker(workflow_api=api, tasks=[task])
        worker._stop_flag = True

        signals = []
        worker.task_progress.connect(lambda *args: signals.append(args))

        worker._process_task(task)

        assert len(signals) == 0
        api.generate_image.assert_not_called()

    @patch.object(GenerationWorker, '_download_video', return_value="/tmp/test.mp4")
    def test_multiple_images_per_prompt(self, mock_dl, tmp_path):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=True)
        api.check_video_status.return_value = _make_status_response()

        task = _make_task(output_folder=str(tmp_path), images_per_prompt=3)
        worker = _make_worker(workflow_api=api, tasks=[task])

        signals = []
        worker.task_progress.connect(lambda *args: signals.append(args))

        worker._process_task(task)

        assert api.generate_image.call_count == 3
        last = signals[-1]
        assert last[2] == "completed"
        assert len(last[3].get("output_images", [])) == 3

    @patch.object(GenerationWorker, '_download_video', return_value="/tmp/test.mp4")
    def test_elapsed_seconds_in_result(self, mock_dl, tmp_path):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=True)
        api.check_video_status.return_value = _make_status_response()

        task = _make_task(output_folder=str(tmp_path))
        worker = _make_worker(workflow_api=api, tasks=[task])

        signals = []
        worker.task_progress.connect(lambda *args: signals.append(args))

        worker._process_task(task)

        last = signals[-1]
        assert "elapsed_seconds" in last[3]
        assert last[3]["elapsed_seconds"] >= 0


class TestGenerationWorkerBatch:
    """Test batch execution (run method)."""

    @patch.object(GenerationWorker, '_download_video', return_value="/tmp/test.mp4")
    def test_batch_all_succeed(self, mock_dl, qtbot, tmp_path):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=True)
        api.check_video_status.return_value = _make_status_response()

        tasks = [_make_task(f"t{i}", i, output_folder=str(tmp_path)) for i in range(3)]
        worker = _make_worker(workflow_api=api, tasks=tasks)

        completed_ids = []
        worker.task_progress.connect(
            lambda tid, p, s, d: completed_ids.append(tid) if s == "completed" else None
        )

        with qtbot.waitSignal(worker.finished_all, timeout=10000):
            worker.start()

        assert len(completed_ids) == 3

    def test_batch_with_failures(self, qtbot):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=False)

        tasks = [_make_task(f"t{i}", i) for i in range(2)]
        worker = _make_worker(workflow_api=api, tasks=tasks)

        error_ids = []
        worker.task_progress.connect(
            lambda tid, p, s, d: error_ids.append(tid) if s == "error" else None
        )

        with qtbot.waitSignal(worker.finished_all, timeout=10000):
            worker.start()

        assert len(error_ids) == 2

    @patch.object(GenerationWorker, '_download_video', return_value="/tmp/test.mp4")
    def test_batch_mixed_success_and_failure(self, mock_dl, qtbot, tmp_path):
        api = MagicMock()
        api.generate_image.side_effect = [
            _make_api_response(success=True),
            _make_api_response(success=False),
        ]
        api.check_video_status.return_value = _make_status_response()

        tasks = [
            _make_task("t1", 1, output_folder=str(tmp_path)),
            _make_task("t2", 2),
        ]
        worker = _make_worker(workflow_api=api, tasks=tasks, concurrency=1)

        results = {}
        worker.task_progress.connect(
            lambda tid, p, s, d: results.update({tid: s}) if s in ("completed", "error") else None
        )

        with qtbot.waitSignal(worker.finished_all, timeout=10000):
            worker.start()

        assert results["t1"] == "completed"
        assert results["t2"] == "error"

    def test_batch_empty_tasks(self, qtbot):
        worker = _make_worker(tasks=[])

        with qtbot.waitSignal(worker.finished_all, timeout=5000):
            worker.start()

    @patch.object(GenerationWorker, '_download_video', return_value="/tmp/test.mp4")
    def test_finished_all_emitted(self, mock_dl, qtbot, tmp_path):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=True)
        api.check_video_status.return_value = _make_status_response()

        tasks = [_make_task("t1", 1, output_folder=str(tmp_path))]
        worker = _make_worker(workflow_api=api, tasks=tasks)

        with qtbot.waitSignal(worker.finished_all, timeout=10000):
            worker.start()

    @patch.object(GenerationWorker, '_download_video', return_value="/tmp/test.mp4")
    def test_concurrency_limit_respected(self, mock_dl, qtbot, tmp_path):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=True)
        api.check_video_status.return_value = _make_status_response()

        tasks = [_make_task(f"t{i}", i, output_folder=str(tmp_path)) for i in range(5)]
        worker = _make_worker(workflow_api=api, tasks=tasks, concurrency=2)

        with qtbot.waitSignal(worker.finished_all, timeout=15000):
            worker.start()

        assert api.generate_image.call_count == 5

    @patch.object(GenerationWorker, '_download_video', return_value="/tmp/test.mp4")
    def test_all_task_ids_reported(self, mock_dl, qtbot, tmp_path):
        api = MagicMock()
        api.generate_image.return_value = _make_api_response(success=True)
        api.check_video_status.return_value = _make_status_response()

        tasks = [_make_task(f"t{i}", i, output_folder=str(tmp_path)) for i in range(4)]
        worker = _make_worker(workflow_api=api, tasks=tasks)

        reported_ids = set()
        worker.task_progress.connect(lambda tid, p, s, d: reported_ids.add(tid))

        with qtbot.waitSignal(worker.finished_all, timeout=10000):
            worker.start()

        assert reported_ids == {"t0", "t1", "t2", "t3"}


class TestGenerationWorkerTimeout:
    """Test per-task timeout behavior."""

    def test_timeout_marks_task_as_error(self, qtbot):
        api = MagicMock()

        def slow_generate(*args, **kwargs):
            time.sleep(5)
            return _make_api_response(success=True)

        api.generate_image.side_effect = slow_generate

        task = _make_task("slow-1", 1)
        worker = _make_worker(workflow_api=api, tasks=[task])
        worker.TASK_TIMEOUT = 1
        worker.POLL_MAX_TIME = 1

        results = {}

        def on_progress(tid, p, s, d):
            if s in ("error", "completed"):
                results[tid] = {"status": s, "data": d}

        worker.task_progress.connect(on_progress)

        with qtbot.waitSignal(worker.finished_all, timeout=15000):
            worker.start()

        assert "slow-1" in results


class TestGenerationWorkerSaveImage:
    """Test _save_image static method."""

    def test_saves_file_to_folder(self, tmp_path):
        encoded = base64.b64encode(b"fake png data").decode()
        path = GenerationWorker._save_image(encoded, str(tmp_path), "", 1, 0)
        assert os.path.exists(path)
        assert path.endswith("001.png")

    def test_creates_output_folder(self, tmp_path):
        new_folder = str(tmp_path / "sub" / "dir")
        encoded = base64.b64encode(b"data").decode()
        path = GenerationWorker._save_image(encoded, new_folder, "", 1, 0)
        assert os.path.exists(new_folder)
        assert os.path.exists(path)

    def test_prefix_in_filename(self, tmp_path):
        encoded = base64.b64encode(b"data").decode()
        path = GenerationWorker._save_image(encoded, str(tmp_path), "scene", 5, 0)
        assert "scene" in os.path.basename(path)
        assert "005" in os.path.basename(path)

    def test_prefix_extension_stripped(self, tmp_path):
        encoded = base64.b64encode(b"data").decode()
        path = GenerationWorker._save_image(encoded, str(tmp_path), "test.png", 1, 0)
        assert not path.endswith(".png.png")
        assert path.endswith(".png")
        assert "test_001" in os.path.basename(path)

    def test_img_idx_in_filename(self, tmp_path):
        encoded = base64.b64encode(b"data").decode()
        path = GenerationWorker._save_image(encoded, str(tmp_path), "", 1, 2)
        assert "3" in os.path.basename(path)

    def test_stt_zero_padded(self, tmp_path):
        encoded = base64.b64encode(b"data").decode()
        path = GenerationWorker._save_image(encoded, str(tmp_path), "", 42, 0)
        assert "042" in os.path.basename(path)

    def test_file_content_matches_decoded(self, tmp_path):
        original = b"test image content bytes"
        encoded = base64.b64encode(original).decode()
        path = GenerationWorker._save_image(encoded, str(tmp_path), "", 1, 0)
        with open(path, "rb") as f:
            assert f.read() == original

    def test_no_prefix_sequential_naming(self, tmp_path):
        encoded = base64.b64encode(b"data").decode()
        path = GenerationWorker._save_image(encoded, str(tmp_path), "", 1, 0)
        assert os.path.basename(path) == "001.png"

    def test_no_prefix_no_img_idx(self, tmp_path):
        encoded = base64.b64encode(b"data").decode()
        path = GenerationWorker._save_image(encoded, str(tmp_path), "", 10, 0)
        assert os.path.basename(path) == "010.png"


class TestGenerationWorkerGetSaveFolder:
    """Test _get_save_folder helper."""

    def test_custom_folder_returned(self):
        worker = _make_worker(workflow_name="Test")
        assert worker._get_save_folder("/custom/path") == "/custom/path"

    def test_workflow_name_in_path(self, tmp_path):
        worker = _make_worker(workflow_name="MyProject")
        with patch("os.path.expanduser", return_value=str(tmp_path)):
            folder = worker._get_save_folder("")
            assert "MyProject" in folder

    def test_sanitized_workflow(self, tmp_path):
        worker = _make_worker(workflow_name="A/B:C")
        with patch("os.path.expanduser", return_value=str(tmp_path)):
            folder = worker._get_save_folder("")
            assert "/" not in os.path.basename(folder)
            assert ":" not in os.path.basename(folder)
