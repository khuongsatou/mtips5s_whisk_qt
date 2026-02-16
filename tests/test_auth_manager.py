"""
Tests for AuthManager and UserSession — session lifecycle, persistence, signals,
login, fetch_user_info, update_user, logout with file cleanup.
"""
import json
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from app.auth.auth_manager import AuthManager, UserSession, SESSION_FILE


class TestUserSession:
    """Test UserSession dataclass."""

    def test_default_session_is_invalid(self):
        session = UserSession()
        assert not session.is_valid

    def test_valid_session(self):
        session = UserSession(access_token="tok123", username="admin")
        assert session.is_valid

    def test_session_missing_token_is_invalid(self):
        session = UserSession(username="admin")
        assert not session.is_valid

    def test_session_missing_username_is_invalid(self):
        session = UserSession(access_token="tok123")
        assert not session.is_valid

    def test_to_dict(self):
        session = UserSession(
            access_token="t1", refresh_token="r1", user_id=42,
            username="admin", name="Admin", mail="a@b.com",
            roles="editor", credit=100, key_code="KEY",
            tools_access={"whisk": True},
        )
        d = session.to_dict()
        assert d["access_token"] == "t1"
        assert d["user_id"] == 42
        assert d["tools_access"] == {"whisk": True}

    def test_to_dict_has_all_fields(self):
        session = UserSession(
            access_token="t", refresh_token="r", user_id=1,
            username="u", name="n", mail="m", roles="ro",
            credit=0, key_code="k", tools_access={},
            status="active", updated_at="2024-01-01", use_credit=True,
        )
        d = session.to_dict()
        assert "status" in d
        assert "updated_at" in d
        assert "use_credit" in d
        assert d["use_credit"] is True

    def test_from_dict(self):
        data = {
            "access_token": "t1", "refresh_token": "r1", "user_id": 42,
            "username": "admin", "name": "Admin", "mail": "a@b.com",
            "roles": "editor", "credit": 100, "key_code": "KEY",
            "tools_access": {"whisk": True},
        }
        session = UserSession.from_dict(data)
        assert session.access_token == "t1"
        assert session.user_id == 42
        assert session.username == "admin"

    def test_from_dict_with_defaults(self):
        session = UserSession.from_dict({})
        assert session.access_token == ""
        assert session.user_id == 0
        assert session.tools_access == {}

    def test_roundtrip_to_dict_from_dict(self):
        original = UserSession(
            access_token="tok", refresh_token="ref", user_id=1,
            username="user", name="User", key_code="K1"
        )
        restored = UserSession.from_dict(original.to_dict())
        assert restored.access_token == original.access_token
        assert restored.username == original.username
        assert restored.user_id == original.user_id


class TestAuthManager:
    """Test AuthManager session lifecycle."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.auth = AuthManager()

    def test_initial_state_not_logged_in(self):
        assert not self.auth.is_logged_in
        assert self.auth.session is None

    def test_logout_when_not_logged_in(self):
        self.auth.logout()
        assert not self.auth.is_logged_in

    def test_logout_emits_signal(self):
        signals = []
        self.auth.logged_out.connect(lambda: signals.append(True))
        self.auth.logout()
        assert len(signals) == 1

    def test_try_restore_no_file(self):
        with patch("app.auth.auth_manager.SESSION_FILE", "/tmp/_non_existent_session.json"):
            result = self.auth.try_restore_session()
        assert not result
        assert not self.auth.is_logged_in

    def test_try_restore_valid_session(self):
        session_data = {
            "access_token": "tok",
            "username": "admin",
            "refresh_token": "ref",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(session_data, f)
            tmp_path = f.name

        try:
            with patch("app.auth.auth_manager.SESSION_FILE", tmp_path):
                result = self.auth.try_restore_session()
            assert result
            assert self.auth.is_logged_in
            assert self.auth.session.username == "admin"
        finally:
            os.unlink(tmp_path)

    def test_try_restore_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json")
            tmp_path = f.name

        try:
            with patch("app.auth.auth_manager.SESSION_FILE", tmp_path):
                result = self.auth.try_restore_session()
            assert not result
        finally:
            os.unlink(tmp_path)

    def test_try_restore_empty_token_does_not_restore(self):
        session_data = {"access_token": "", "username": ""}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(session_data, f)
            tmp_path = f.name

        try:
            with patch("app.auth.auth_manager.SESSION_FILE", tmp_path):
                result = self.auth.try_restore_session()
            assert not result
        finally:
            os.unlink(tmp_path)

    def test_logout_clears_session(self):
        self.auth._session = UserSession(access_token="tok", username="user")
        assert self.auth.is_logged_in
        self.auth.logout()
        assert not self.auth.is_logged_in
        assert self.auth.session is None

    def test_logout_removes_session_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"access_token": "t", "username": "u"}, f)
            tmp_path = f.name
        self.auth._session = UserSession(access_token="t", username="u")
        with patch("app.auth.auth_manager.SESSION_FILE", tmp_path):
            self.auth.logout()
        assert not os.path.exists(tmp_path)


class TestAuthManagerLogin:
    """Test AuthManager.login() with mocked HTTP calls."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.auth = AuthManager()

    def _mock_urlopen_success(self):
        """Create a mock response for successful login."""
        body = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "message": "Login successful",
            "data": {
                "id": 99,
                "username": "testuser",
                "name": "Test User",
                "mail": "test@example.com",
                "roles": "admin",
                "credit": 500,
                "tools_access": {"whisk": True},
                "status": "active",
                "updated_at": "2024-01-01",
                "use_credit": False,
            },
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(body).encode("utf-8")
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_login_success(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_urlopen_success()

        signals = []
        self.auth.login_success.connect(lambda s: signals.append(s))

        with patch.object(self.auth, "_save_session"):
            success, message = self.auth.login("my_key_code")

        assert success is True
        assert "successful" in message.lower() or "Login" in message
        assert self.auth.is_logged_in
        assert self.auth.session.username == "testuser"
        assert self.auth.session.access_token == "new_access"
        assert self.auth.session.user_id == 99
        assert len(signals) == 1

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_login_http_error_with_json_body(self, mock_urlopen):
        import urllib.error
        error_body = json.dumps({"message": "Invalid key code"}).encode("utf-8")
        mock_error = urllib.error.HTTPError(
            url="http://test", code=401, msg="Unauthorized",
            hdrs=None, fp=MagicMock(read=MagicMock(return_value=error_body)),
        )
        mock_error.read = MagicMock(return_value=error_body)
        mock_urlopen.side_effect = mock_error

        signals = []
        self.auth.login_failed.connect(lambda m: signals.append(m))

        success, message = self.auth.login("bad_key")

        assert success is False
        assert "Invalid key code" in message
        assert len(signals) == 1

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_login_http_error_without_json_body(self, mock_urlopen):
        import urllib.error
        mock_error = urllib.error.HTTPError(
            url="http://test", code=500, msg="Server Error",
            hdrs=None, fp=MagicMock(read=MagicMock(return_value=b"not json")),
        )
        mock_error.read = MagicMock(return_value=b"not json")
        mock_urlopen.side_effect = mock_error

        success, message = self.auth.login("key")
        assert success is False
        assert "500" in message

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_login_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        signals = []
        self.auth.login_failed.connect(lambda m: signals.append(m))

        success, message = self.auth.login("key")
        assert success is False
        assert "Cannot connect" in message
        assert len(signals) == 1

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_login_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("unexpected")

        success, message = self.auth.login("key")
        assert success is False
        assert "unexpected" in message


class TestAuthManagerFetchAndUpdate:
    """Test fetch_user_info and update_user with mocked HTTP."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.auth = AuthManager()
        self.auth._session = UserSession(
            access_token="tok123", username="admin", user_id=42,
        )

    def test_fetch_user_info_no_session(self):
        self.auth._session = None
        assert self.auth.fetch_user_info() is False

    def test_fetch_user_info_no_token(self):
        self.auth._session = UserSession(username="admin")
        assert self.auth.fetch_user_info() is False

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_fetch_user_info_success(self, mock_urlopen):
        body = {
            "username": "admin_updated", "name": "New Name",
            "credit": 999, "roles": "superadmin",
            "mail": "new@test.com", "tools_access": {"whisk": True},
            "status": "active", "updated_at": "2024-06",
            "use_credit": True,
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(body).encode("utf-8")
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with patch.object(self.auth, "_save_session"):
            result = self.auth.fetch_user_info()

        assert result is True
        assert self.auth.session.username == "admin_updated"
        assert self.auth.session.credit == 999

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_fetch_user_info_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("network error")
        result = self.auth.fetch_user_info()
        assert result is False

    def test_update_user_not_logged_in(self):
        self.auth._session = None
        success, msg = self.auth.update_user(name="new")
        assert success is False
        assert "Not logged in" in msg

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_update_user_success(self, mock_urlopen):
        body = {
            "message": "Updated successfully",
            "data": {
                "name": "Updated Name",
                "credit": 1000,
                "tools_access": {},
                "status": "active",
                "updated_at": "2024-06-01",
                "use_credit": True,
            },
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(body).encode("utf-8")
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with patch.object(self.auth, "_save_session"):
            success, msg = self.auth.update_user(name="Updated Name")

        assert success is True
        assert self.auth.session.name == "Updated Name"
        assert self.auth.session.credit == 1000

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_update_user_http_error(self, mock_urlopen):
        import urllib.error
        error_body = json.dumps({"message": "Forbidden"}).encode("utf-8")
        mock_error = urllib.error.HTTPError(
            url="http://test", code=403, msg="Forbidden",
            hdrs=None, fp=MagicMock(read=MagicMock(return_value=error_body)),
        )
        mock_error.read = MagicMock(return_value=error_body)
        mock_urlopen.side_effect = mock_error

        success, msg = self.auth.update_user(name="x")
        assert success is False
        assert "Forbidden" in msg

    @patch("app.auth.auth_manager.urllib.request.urlopen")
    def test_update_user_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("boom")
        success, msg = self.auth.update_user(name="x")
        assert success is False
        assert "boom" in msg


class TestAuthManagerSaveSession:
    """Test _save_session persistence."""

    def test_save_session_writes_file(self):
        auth = AuthManager()
        auth._session = UserSession(access_token="t", username="u")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            tmp_path = f.name
        try:
            with patch("app.auth.auth_manager.SESSION_FILE", tmp_path):
                auth._save_session()
            with open(tmp_path) as f:
                data = json.load(f)
            assert data["access_token"] == "t"
            assert data["username"] == "u"
        finally:
            os.unlink(tmp_path)

    def test_save_session_no_session(self):
        auth = AuthManager()
        auth._session = None
        # Should not raise
        auth._save_session()
