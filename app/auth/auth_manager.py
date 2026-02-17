"""
Whisk Desktop — Auth Manager.

Handles login via key_code, token persistence, and session management.
Stores session in ~/.whisk_session.json for auto-login.
"""
import json
import os
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger("whisk.auth")

from app.api.api_config import admin_url

SESSION_FILE = os.path.join(os.path.expanduser("~"), ".whisk_session.json")
LOGIN_URL = admin_url("auth/login-by-key")
ME_URL = admin_url("auth/me")
UPDATE_URL = admin_url("auth")
REFRESH_URL = admin_url("auth/refresh")
LOGOUT_URL = admin_url("auth/logout")


@dataclass
class UserSession:
    """Represents a logged-in user session."""
    access_token: str = ""
    refresh_token: str = ""
    user_id: int = 0
    username: str = ""
    name: str = ""
    mail: str = ""
    roles: str = ""
    credit: int = 0
    key_code: str = ""
    tools_access: dict = field(default_factory=dict)
    status: str = ""
    updated_at: str = ""
    use_credit: bool = False

    @property
    def is_valid(self) -> bool:
        return bool(self.access_token and self.username)

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user_id": self.user_id,
            "username": self.username,
            "name": self.name,
            "mail": self.mail,
            "roles": self.roles,
            "credit": self.credit,
            "key_code": self.key_code,
            "tools_access": self.tools_access,
            "status": self.status,
            "updated_at": self.updated_at,
            "use_credit": self.use_credit,
        }

    @staticmethod
    def from_dict(data: dict) -> "UserSession":
        return UserSession(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            user_id=data.get("user_id", 0),
            username=data.get("username", ""),
            name=data.get("name", ""),
            mail=data.get("mail", ""),
            roles=data.get("roles", ""),
            credit=data.get("credit", 0),
            key_code=data.get("key_code", ""),
            tools_access=data.get("tools_access", {}),
            status=data.get("status", ""),
            updated_at=data.get("updated_at", ""),
            use_credit=data.get("use_credit", False),
        )


class AuthManager(QObject):
    """Manages authentication, token storage, and session lifecycle."""

    login_success = Signal(object)   # Emits UserSession
    login_failed = Signal(str)       # Emits error message
    logged_out = Signal()
    on_token_refreshed = Signal(str)  # Emits new access_token

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session: Optional[UserSession] = None

    @property
    def session(self) -> Optional[UserSession]:
        return self._session

    @property
    def is_logged_in(self) -> bool:
        return self._session is not None and self._session.is_valid

    def try_restore_session(self) -> bool:
        """Try to restore session with auto-recovery cascade.

        Recovery order:
        1. Load session from disk → validate with /auth/me
        2. If access_token expired → refresh with refresh_token
        3. If refresh_token expired → re-login with saved key_code
        4. If all fail → return False (show login dialog)
        """
        try:
            if not os.path.exists(SESSION_FILE):
                return False
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
            session = UserSession.from_dict(data)
            if not (session.access_token or session.key_code):
                return False

            self._session = session

            # Step 1: Validate current access_token via /auth/me
            if self._session.access_token and self.fetch_user_info():
                logger.info("✅ Session restored — access token valid")
                self.login_success.emit(self._session)
                return True

            # Step 2: Try refresh_token
            if self._session.refresh_token:
                success, _ = self.refresh_token()
                if success:
                    self.fetch_user_info()  # Update user info with new token
                    logger.info("🔄 Session restored via token refresh")
                    self.login_success.emit(self._session)
                    return True

            # Step 3: Re-login with saved key_code
            saved_key = self._session.key_code
            if saved_key:
                logger.info("🔑 Attempting auto-login with saved key_code...")
                self._session = None  # Clear expired session
                success, msg = self.login(saved_key)
                if success:
                    logger.info("✅ Auto-login with key_code successful")
                    # login() already emits login_success
                    return True
                logger.warning(f"❌ Auto-login with key_code failed: {msg}")

            # All recovery steps failed
            self._session = None
            return False

        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.warning(f"⚠️ Failed to restore session file: {e}")
            return False

    def login(self, key_code: str) -> tuple:
        """
        Login with key_code via API.
        Returns (success, message).
        """
        try:
            payload = json.dumps({"key_code": key_code}).encode("utf-8")
            req = urllib.request.Request(
                LOGIN_URL,
                data=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            # Log request (curl-style)
            logger.info(f"📤 >>> POST {LOGIN_URL}")
            logger.debug(f'📤 >>> curl -X POST "{LOGIN_URL}" '
                         f'-H "Content-Type: application/json" '
                         f'-d \'{payload.decode()}\''
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_data = resp.read().decode("utf-8")
                status = resp.status
                body = json.loads(resp_data)

            # Log response
            logger.info(f"📥 <<< {status} OK")
            logger.debug(f"📥 <<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            user_data = body.get("data", {})

            self._session = UserSession(
                access_token=body.get("access_token", ""),
                refresh_token=body.get("refresh_token", ""),
                user_id=user_data.get("id", 0),
                username=user_data.get("username", ""),
                name=user_data.get("name", ""),
                mail=user_data.get("mail", ""),
                roles=user_data.get("roles", ""),
                credit=user_data.get("credit", 0),
                key_code=key_code,
                tools_access=user_data.get("tools_access", {}),
                status=user_data.get("status", ""),
                updated_at=user_data.get("updated_at", ""),
                use_credit=user_data.get("use_credit", False),
            )

            self._save_session()
            self.login_success.emit(self._session)
            return True, body.get("message", "Login successful")

        except urllib.error.HTTPError as e:
            try:
                error_data = e.read().decode("utf-8")
                error_body = json.loads(error_data)
                error_msg = error_body.get("message", f"HTTP {e.code}")
            except Exception:
                error_data = ""
                error_msg = f"HTTP {e.code}"
            logger.error(f"❌ <<< {e.code} Error")
            logger.debug(f"📥 <<< Response: {error_data}")
            self.login_failed.emit(error_msg)
            return False, error_msg

        except urllib.error.URLError as e:
            msg = "Cannot connect to server"
            logger.error(f"❌ <<< Connection failed: {e.reason}")
            self.login_failed.emit(msg)
            return False, msg

        except Exception as e:
            msg = str(e)
            logger.error(f"❌ <<< Exception: {msg}")
            self.login_failed.emit(msg)
            return False, msg

    def logout(self):
        """Call server-side logout, then clear local session and file."""
        # Fire-and-forget server logout (don't block on failure)
        if self._session and self._session.access_token:
            try:
                req = urllib.request.Request(
                    LOGOUT_URL,
                    data=b"",
                    headers={
                        "Accept": "application/json",
                        "Authorization": f"Bearer {self._session.access_token}",
                    },
                    method="POST",
                )
                logger.info(f"📤 >>> POST {LOGOUT_URL}")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                logger.info(f"📥 <<< {resp.status} {body.get('message', 'OK')}")
            except Exception as e:
                logger.warning(f"⚠️ Server logout failed (ignored): {e}")

        self._session = None
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
        except IOError:
            pass
        self.logged_out.emit()

    def refresh_token(self) -> tuple[bool, str]:
        """
        Refresh access_token using the stored refresh_token.
        Calls POST /auth/refresh with refresh_token in Bearer header.
        Returns (success, new_access_token_or_error_message).
        """
        if not self._session or not self._session.refresh_token:
            return False, "No refresh token available"

        try:
            req = urllib.request.Request(
                REFRESH_URL,
                data=b"",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self._session.refresh_token}",
                },
                method="POST",
            )
            logger.info(f"📤 >>> POST {REFRESH_URL}")

            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            new_token = body.get("access_token", "")
            if not new_token:
                return False, "Server returned empty access_token"

            logger.info(f"📥 <<< {resp.status} Token refreshed")
            self._session.access_token = new_token
            self._save_session()
            self.on_token_refreshed.emit(new_token)
            return True, new_token

        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode("utf-8"))
                error_msg = error_body.get("message", f"HTTP {e.code}")
            except Exception:
                error_msg = f"HTTP {e.code}"
            logger.error(f"❌ <<< Refresh failed: {e.code} {error_msg}")
            return False, error_msg

        except urllib.error.URLError as e:
            msg = "Cannot connect to server"
            logger.error(f"❌ <<< Refresh connection failed: {e.reason}")
            return False, msg

        except Exception as e:
            msg = str(e)
            logger.error(f"❌ <<< Refresh exception: {msg}")
            return False, msg

    def fetch_user_info(self) -> bool:
        """Fetch current user info from /auth/me and update session."""
        if not self._session or not self._session.access_token:
            return False
        try:
            req = urllib.request.Request(
                ME_URL,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self._session.access_token}",
                },
                method="GET",
            )
            logger.info(f"📤 >>> GET {ME_URL}")
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            logger.info(f"📥 <<< {resp.status} OK")
            logger.debug(f"📥 <<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            # Update session fields from /auth/me response
            self._session.username = body.get("username", self._session.username)
            self._session.name = body.get("name", self._session.name)
            self._session.mail = body.get("mail", self._session.mail)
            self._session.roles = body.get("roles", self._session.roles)
            self._session.credit = body.get("credit", self._session.credit)
            self._session.tools_access = body.get("tools_access", self._session.tools_access)
            self._session.status = body.get("status", self._session.status)
            self._session.updated_at = body.get("updated_at", self._session.updated_at)
            self._session.use_credit = body.get("use_credit", self._session.use_credit)
            self._save_session()
            return True
        except Exception as e:
            logger.error(f"❌ <<< fetch_user_info failed: {e}")
            return False

    def update_user(self, **fields) -> tuple:
        """
        Update user settings via PATCH /auth/{user_id}.
        Returns (success, message).
        """
        if not self._session or not self._session.access_token:
            return False, "Not logged in"
        try:
            url = f"{UPDATE_URL}/{self._session.user_id}"
            payload = json.dumps(fields).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._session.access_token}",
                },
                method="PATCH",
            )
            logger.info(f"📤 >>> PATCH {url}")
            logger.debug(f"📤 >>> Body: {fields}")

            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"📥 <<< {resp.status} OK")
            logger.debug(f"📥 <<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            # Update session from response data
            data = body.get("data", {})
            if data:
                self._session.name = data.get("name", self._session.name)
                self._session.credit = data.get("credit", self._session.credit)
                self._session.tools_access = data.get("tools_access", self._session.tools_access)
                self._session.status = data.get("status", self._session.status)
                self._session.updated_at = data.get("updated_at", self._session.updated_at)
                self._session.use_credit = data.get("use_credit", self._session.use_credit)
                self._save_session()

            return True, body.get("message", "Updated successfully")

        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode("utf-8"))
                error_msg = error_body.get("message", f"HTTP {e.code}")
            except Exception:
                error_msg = f"HTTP {e.code}"
            logger.error(f"❌ <<< {e.code} Error: {error_msg}")
            return False, error_msg

        except Exception as e:
            msg = str(e)
            logger.error(f"❌ <<< update_user failed: {msg}")
            return False, msg

    def _save_session(self):
        """Persist session to disk."""
        if self._session:
            try:
                with open(SESSION_FILE, "w") as f:
                    json.dump(self._session.to_dict(), f, indent=2)
            except IOError:
                pass

