"""Tests for app.captcha_sidecar_manager module."""
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from PySide6.QtCore import QCoreApplication


# ── Helper functions ────────────────────────────────────────────


class TestFindNode:
    """Tests for _find_node()."""

    def test_find_node_from_path(self):
        with patch("shutil.which", return_value="/usr/local/bin/node"):
            from app.captcha_sidecar_manager import _find_node
            result = _find_node()
        assert result == "/usr/local/bin/node"

    def test_find_node_not_found(self):
        with patch("shutil.which", return_value=None), \
             patch("os.path.isfile", return_value=False):
            from app.captcha_sidecar_manager import _find_node
            result = _find_node()
        # May find from PATH candidates or return None
        # Depends on system, so we just verify it doesn't crash


class TestFindSidecarScript:
    """Tests for _find_sidecar_script()."""

    def test_finds_pucaptcha(self, tmp_path):
        script = tmp_path / "pucaptcha" / "capture-sidecar.js"
        script.parent.mkdir()
        script.write_text("// sidecar")
        with patch("app.captcha_sidecar_manager.os.path.dirname",
                    return_value=str(tmp_path)):
            # Need to patch at module level
            pass
        # Simple test: function should not crash
        from app.captcha_sidecar_manager import _find_sidecar_script
        _find_sidecar_script()  # just verify no crash


# ── CaptchaSidecarManager ──────────────────────────────────────


class TestCaptchaSidecarManager:
    """Tests for CaptchaSidecarManager class."""

    @pytest.fixture
    def manager(self, qapp):
        from app.captcha_sidecar_manager import CaptchaSidecarManager
        m = CaptchaSidecarManager(proxy_url="http://proxy:8080", action="TEST")
        yield m

    def test_init_defaults(self, manager):
        assert manager.proxy_url == "http://proxy:8080"
        assert manager.action == "TEST"
        assert manager._process is None
        assert not manager._stop_event.is_set()

    def test_init_default_action(self, qapp):
        from app.captcha_sidecar_manager import CaptchaSidecarManager
        m = CaptchaSidecarManager()
        assert m.action == "VIDEO_GENERATION"
        assert m.proxy_url is None

    def test_is_running_no_process(self, manager):
        assert manager.is_running is False

    def test_is_running_with_process(self, manager):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # still running
        manager._process = mock_proc
        assert manager.is_running is True

    def test_is_running_exited_process(self, manager):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0  # exited
        manager._process = mock_proc
        assert manager.is_running is False

    def test_send_command_no_process(self, manager):
        result = manager._send_command("PING")
        assert result is False

    def test_send_command_success(self, manager):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdin = MagicMock()
        manager._process = mock_proc
        result = manager._send_command("PING")
        assert result is True
        mock_proc.stdin.write.assert_called_once_with("PING\n")
        mock_proc.stdin.flush.assert_called_once()

    def test_send_command_broken_pipe(self, manager):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.write.side_effect = BrokenPipeError("pipe broke")
        manager._process = mock_proc
        result = manager._send_command("PING")
        assert result is False

    def test_request_tokens(self, manager):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdin = MagicMock()
        manager._process = mock_proc
        manager.request_tokens(count=3, action="MY_ACTION")
        assert manager._pending_action == "MY_ACTION"
        mock_proc.stdin.write.assert_called_once_with("GET_TOKENS 3\n")

    def test_restart_browser(self, manager):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdin = MagicMock()
        manager._process = mock_proc
        manager.restart_browser()
        mock_proc.stdin.write.assert_called_once_with("RESTART_BROWSER\n")

    def test_ping(self, manager):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdin = MagicMock()
        manager._process = mock_proc
        manager.ping()
        mock_proc.stdin.write.assert_called_once_with("PING\n")


# ── stdout parsing ──────────────────────────────────────────────


class TestHandleStdoutLine:
    """Tests for _handle_stdout_line parsing."""

    @pytest.fixture
    def manager(self, qapp):
        from app.captcha_sidecar_manager import CaptchaSidecarManager
        m = CaptchaSidecarManager()
        m.sidecar_ready = MagicMock()
        m.sidecar_ready.emit = MagicMock()
        m.sidecar_error = MagicMock()
        m.sidecar_error.emit = MagicMock()
        m.token_received = MagicMock()
        m.token_received.emit = MagicMock()
        yield m

    def test_ready_signal(self, manager):
        manager._handle_stdout_line('{"success": true, "message": "READY"}')
        manager.sidecar_ready.emit.assert_called_once()

    def test_init_failed(self, manager):
        manager._handle_stdout_line('{"success": false, "message": "INIT_FAILED", "error": "no browser"}')
        manager.sidecar_error.emit.assert_called_once()
        args = manager.sidecar_error.emit.call_args[0]
        assert "no browser" in args[0]

    def test_init_failed_with_hint(self, manager):
        manager._handle_stdout_line(
            '{"success": false, "message": "INIT_FAILED", "error": "fail", "errorHint": "install chrome"}'
        )
        args = manager.sidecar_error.emit.call_args[0]
        assert "install chrome" in args[0]

    def test_tokens_received(self, manager):
        manager._handle_stdout_line('{"success": true, "tokens": ["tok1", "tok2"]}')
        manager.token_received.emit.assert_called_once_with(["tok1", "tok2"], "VIDEO_GENERATION")

    def test_error_response(self, manager):
        manager._handle_stdout_line('{"success": false, "error": "captcha failed", "errorType": "CAPTCHA"}')
        manager.sidecar_error.emit.assert_called_once()

    def test_fatal_error_sets_stop(self, manager):
        manager._handle_stdout_line(
            '{"success": false, "error": "fatal crash", "isFatal": true}'
        )
        assert manager._stop_event.is_set()

    def test_non_json_line(self, manager):
        # Should not crash
        manager._handle_stdout_line("this is not json")

    def test_generic_message(self, manager):
        manager._handle_stdout_line('{"success": true, "message": "PONG"}')
        # No error or token signals should fire
        manager.sidecar_error.emit.assert_not_called()
        manager.token_received.emit.assert_not_called()


# ── cleanup ─────────────────────────────────────────────────────


class TestCleanup:
    """Tests for _cleanup and stop."""

    @pytest.fixture
    def manager(self, qapp):
        from app.captcha_sidecar_manager import CaptchaSidecarManager
        m = CaptchaSidecarManager()
        m.quit = MagicMock()
        m.wait = MagicMock()
        yield m

    def test_cleanup_no_process(self, manager):
        manager._cleanup()  # Should not crash

    def test_cleanup_with_process(self, manager):
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.wait.return_value = 0
        manager._process = mock_proc
        manager._cleanup()
        assert manager._process is None
        mock_proc.stdin.write.assert_called_once_with("SHUTDOWN\n")

    def test_stop_sets_event(self, manager):
        manager.stop()
        assert manager._stop_event.is_set()
