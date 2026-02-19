"""Tests for app.captcha_bridge_server module."""
import json
import queue
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from PySide6.QtCore import QCoreApplication


# ── CaptchaBridgeServer (QThread wrapper) ───────────────────────


class TestCaptchaBridgeServer:
    """Tests for CaptchaBridgeServer class (state management, no HTTP)."""

    @pytest.fixture
    def bridge(self, qapp):
        from app.captcha_bridge_server import CaptchaBridgeServer
        b = CaptchaBridgeServer(port=0)  # port=0 for testing only
        yield b

    def test_init_defaults(self, bridge):
        assert bridge.project_name == ''
        assert all(v is None for v in bridge.pending_requests.values())
        assert bridge.total_tokens_received == 0
        assert bridge._last_token == ''
        assert bridge._stored_cookie == ''
        assert len(bridge._token_queues) == 5
        for ch in range(1, 6):
            assert isinstance(bridge._token_queues[ch], queue.Queue)

    def test_set_project_name(self, bridge):
        bridge.set_project_name("MyProject")
        assert bridge.project_name == "MyProject"

    def test_set_project_name_empty(self, bridge):
        bridge.set_project_name("")
        assert bridge.project_name == ""

    def test_set_project_name_none(self, bridge):
        bridge.set_project_name(None)
        assert bridge.project_name == ""

    def test_request_token(self, bridge):
        bridge.request_token(action="TEST_ACTION", count=3, channel=2)
        assert bridge.pending_requests[2] is not None
        assert bridge.pending_requests[2]["action"] == "TEST_ACTION"
        assert bridge.pending_requests[2]["count"] == 3
        # Other channels should be unaffected
        assert bridge.pending_requests[1] is None

    def test_request_token_defaults(self, bridge):
        bridge.request_token()
        assert bridge.pending_requests[1]["action"] == "VIDEO_GENERATION"
        assert bridge.pending_requests[1]["count"] == 1

    def test_clear_request_single(self, bridge):
        bridge.request_token(channel=3)
        bridge.clear_request(channel=3)
        assert bridge.pending_requests[3] is None

    def test_clear_request_all(self, bridge):
        bridge.request_token(channel=1)
        bridge.request_token(channel=3)
        bridge.clear_request()  # Clear all
        assert all(v is None for v in bridge.pending_requests.values())

    def test_token_queue_put_and_get(self, bridge):
        """Verify token queue is FIFO and per-channel."""
        q1 = bridge.get_token_queue(1)
        q2 = bridge.get_token_queue(2)
        q1.put("token_A")
        q2.put("token_B")
        assert q1.get_nowait() == "token_A"
        assert q2.get_nowait() == "token_B"

    def test_token_queue_get_timeout(self, bridge):
        """Empty queue should raise on get with timeout."""
        q = bridge.get_token_queue(1)
        with pytest.raises(queue.Empty):
            q.get(timeout=0.05)

    def test_get_token_queue_clamping(self, bridge):
        """Channel values are clamped to 1..5."""
        assert bridge.get_token_queue(0) is bridge.get_token_queue(1)
        assert bridge.get_token_queue(99) is bridge.get_token_queue(5)

    def test_stop_sets_event(self, bridge):
        """stop() should set the stop event."""
        assert not bridge._stop_event.is_set()
        # Mock quit/wait to avoid QThread issues
        bridge.quit = MagicMock()
        bridge.wait = MagicMock()
        bridge.stop()
        assert bridge._stop_event.is_set()


# ── CaptchaBridgeHandler (HTTP endpoints) ───────────────────────


class TestCaptchaBridgeHandler:
    """Test HTTP handler logic via direct method calls."""

    @pytest.fixture
    def handler_env(self, qapp):
        """Create a mock handler with a mock bridge server."""
        from app.captcha_bridge_server import CaptchaBridgeHandler, CaptchaBridgeServer

        bridge = CaptchaBridgeServer(port=0)
        bridge.project_name = "TestProject"
        bridge.total_tokens_received = 5

        # Create mock server object
        mock_server = MagicMock()
        mock_server.bridge = bridge

        # Create handler instance without actually handling a request
        handler = CaptchaBridgeHandler.__new__(CaptchaBridgeHandler)
        handler.server = mock_server
        handler.headers = {}

        # Mock response methods
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        import io
        handler.wfile = io.BytesIO()

        return handler, bridge

    def test_send_json(self, handler_env):
        handler, bridge = handler_env
        handler._send_json(200, {"status": "ok"})
        handler.send_response.assert_called_once_with(200)
        output = handler.wfile.getvalue()
        data = json.loads(output.decode("utf-8"))
        assert data["status"] == "ok"

    def test_do_get_captcha_status(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/captcha/status"
        handler.do_GET()
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert output["running"] is True
        assert output["has_pending"] is False
        assert output["tokens_received"] == 5
        assert output["project_name"] == "TestProject"
        assert "channels" in output

    def test_do_get_captcha_status_with_pending(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/captcha/status?channel=2"
        bridge.request_token(action="TEST", count=1, channel=2)
        handler.do_GET()
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert output["has_pending"] is True
        assert output["channel"] == 2

    def test_do_get_bridge_info(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/bridge/info"
        handler.do_GET()
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert output["project_name"] == "TestProject"
        assert output["running"] is True
        assert output["num_channels"] == 5

    def test_do_get_bridge_cookie(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/bridge/cookie"
        bridge._stored_cookie = "test_cookie_value"
        handler.do_GET()
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert output["cookie"] == "test_cookie_value"
        assert output["has_cookie"] is True

    def test_do_get_bridge_cookie_empty(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/bridge/cookie"
        bridge._stored_cookie = ""
        handler.do_GET()
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert output["has_cookie"] is False

    def test_do_get_captcha_request_none(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/captcha/request?channel=1"
        handler.do_GET()
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert output["need_token"] is False
        assert output["channel"] == 1

    def test_do_get_captcha_request_pending(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/captcha/request?channel=3"
        bridge.request_token(action="VIDEO_GENERATION", count=2, channel=3)
        handler.do_GET()
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert output["need_token"] is True
        assert output["action"] == "VIDEO_GENERATION"
        assert output["count"] == 2
        assert output["channel"] == 3

    def test_do_get_404(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/nonexistent"
        handler.do_GET()
        handler.send_response.assert_called_with(404)

    def test_do_post_captcha_token(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/captcha/token"

        # Set up body with channel
        body = json.dumps({
            "tokens": ["tok_A", "tok_B"],
            "action": "TEST",
            "channel": 2,
        }).encode()
        handler.headers = MagicMock()
        handler.headers.get = MagicMock(return_value=str(len(body)))

        import io
        handler.rfile = io.BytesIO(body)

        # Mock the signal emit
        bridge.token_received = MagicMock()
        bridge.token_received.emit = MagicMock()

        # Set pending request on channel 2
        bridge.request_token(channel=2)

        handler.do_POST()

        assert bridge.total_tokens_received == 7  # was 5, +2
        assert bridge._last_token == "tok_A"
        q = bridge.get_token_queue(2)
        assert q.get_nowait() == "tok_A"
        assert q.get_nowait() == "tok_B"
        assert bridge.pending_requests[2] is None
        bridge.token_received.emit.assert_called_once_with(["tok_A", "tok_B"], "TEST", 2)

    def test_do_post_captcha_token_empty(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/captcha/token"

        body = json.dumps({"tokens": []}).encode()
        handler.headers = MagicMock()
        handler.headers.get = MagicMock(return_value=str(len(body)))

        import io
        handler.rfile = io.BytesIO(body)
        handler.do_POST()

        handler.send_response.assert_called_with(400)

    def test_do_post_bridge_cookie(self, handler_env):
        handler, bridge = handler_env
        handler.path = "/bridge/cookie"

        body = json.dumps({"cookie": "my_cookie"}).encode()
        handler.headers = MagicMock()
        handler.headers.get = MagicMock(return_value=str(len(body)))

        import io
        handler.rfile = io.BytesIO(body)
        handler.do_POST()

        assert bridge._stored_cookie == "my_cookie"

    def test_log_message_suppresses_polling(self, handler_env):
        handler, _ = handler_env
        # These should not raise or produce output
        handler.log_message("GET /captcha/request HTTP/1.1 200")
        handler.log_message("GET /bridge/cookie HTTP/1.1 200")
        handler.log_message("GET /bridge/info HTTP/1.1 200")

    def test_do_options_cors(self, handler_env):
        handler, _ = handler_env
        handler.do_OPTIONS()
        handler.send_response.assert_called_with(200)


# ── HTML builders ───────────────────────────────────────────────


class TestHTMLBuilders:
    """Test that HTML page builders return valid HTML."""

    @pytest.fixture
    def bridge(self, qapp):
        from app.captcha_bridge_server import CaptchaBridgeServer
        b = CaptchaBridgeServer(port=18923)
        b.project_name = "Test Project"
        return b

    def test_build_login_page(self, bridge):
        from app.captcha_bridge_server import CaptchaBridgeHandler
        html = CaptchaBridgeHandler._build_login_page(bridge)
        assert "<html" in html.lower()
        assert "Test Project" in html

    def test_build_landing_page(self, bridge):
        from app.captcha_bridge_server import CaptchaBridgeHandler
        html = CaptchaBridgeHandler._build_landing_page(bridge)
        assert "<html" in html.lower()
        assert "Test Project" in html
        assert "18923" in html
