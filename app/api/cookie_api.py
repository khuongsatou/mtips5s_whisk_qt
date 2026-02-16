"""
Whisk Desktop — Cookie/API-Key API Client.

Real HTTP client for cookie management endpoints:
- Test cookie validity (POST /api-keys/test)
- Save/create cookie as api-key (POST /tools/token/frame/run?type=WHISK)
- List api-keys/cookies (GET /api-keys)
"""
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from app.api.api_config import flow_url
from app.api.models import ApiResponse

logger = logging.getLogger("whisk.cookie_api")


class CookieApiClient:
    """HTTP client for cookie/api-key CRUD operations."""

    def __init__(self, access_token: str = ""):
        self._access_token = access_token

    def set_access_token(self, token: str):
        """Update the Bearer token used for all requests."""
        self._access_token = token

    def _headers(self, with_content_type: bool = False) -> dict:
        """Build common request headers."""
        h = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }
        if with_content_type:
            h["Content-Type"] = "application/json"
        return h

    # ── Test Cookie ───────────────────────────────────────────────────

    def test_cookie(self, data: dict) -> ApiResponse:
        """
        POST /api-keys/test — Test cookie validity.

        Args:
            data: Must include:
                - cookies: dict with session-token and csrf-token
                - label: str
                - flow_id: int
                - provider: str (defaults to "WHISK")
                Optional:
                - create_new: bool (default False)
                - timeout: int (default 10)

        Returns:
            ApiResponse with provider_info (user_email, user_name, expires, etc.)
        """
        if "provider" not in data:
            data["provider"] = "WHISK"

        url = flow_url("api-keys/test")
        payload = json.dumps(data).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers=self._headers(with_content_type=True),
                method="POST",
            )

            logger.info(f">>> POST {url}")
            logger.debug(f">>> Body: {json.dumps(data, indent=2, ensure_ascii=False)}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"<<< {resp.status} OK")
            logger.debug(f"<<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            ok = body.get("ok", False)
            return ApiResponse(
                success=ok,
                data=body,
                message=body.get("msg_error", "") if not ok else "Cookie is valid",
            )

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "test_cookie")
        except urllib.error.URLError as e:
            logger.error(f"<<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to server")
        except Exception as e:
            logger.error(f"<<< test_cookie exception: {e}")
            return ApiResponse(success=False, message=str(e))

    # ── Save Cookie (Create API Key) ──────────────────────────────────

    def save_cookie(self, data: dict) -> ApiResponse:
        """
        POST /tools/token/frame/run?type=WHISK — Save cookie as api-key.

        Args:
            data: Must include:
                - cookies: dict with session-token and csrf-token
                - label: str
                - flow_id: int
                Optional:
                - create_new: bool (default True)

        Returns:
            ApiResponse with api_key data, session info, etc.
        """
        provider = data.pop("provider", "WHISK")
        params = urllib.parse.urlencode({"type": provider})
        url = f"{flow_url('tools/token/frame/run')}?{params}"
        payload = json.dumps(data).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers=self._headers(with_content_type=True),
                method="POST",
            )

            logger.info(f">>> POST {url}")
            logger.debug(f">>> Body: {json.dumps(data, indent=2, ensure_ascii=False)}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"<<< {resp.status} OK")
            logger.debug(f"<<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            status = body.get("status", "")
            return ApiResponse(
                success=(status == "ok"),
                data=body,
                message=body.get("message", ""),
            )

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "save_cookie")
        except urllib.error.URLError as e:
            logger.error(f"<<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to server")
        except Exception as e:
            logger.error(f"<<< save_cookie exception: {e}")
            return ApiResponse(success=False, message=str(e))

    # ── List API Keys / Cookies ───────────────────────────────────────

    def get_api_keys(
        self,
        flow_id: int,
        provider: str = "WHISK",
        offset: int = 0,
        limit: int = 1000,
        status: str = "ALL",
        mine: bool = True,
        sort: str = "updated_at:desc",
    ) -> ApiResponse:
        """
        GET /api-keys — List api-keys/cookies with filtering.

        Returns:
            ApiResponse with data = {items: [...], total, offset, limit}.
        """
        params = urllib.parse.urlencode({
            "provider": provider,
            "offset": offset,
            "limit": limit,
            "status": status,
            "mine": str(mine).lower(),
            "sort": sort,
            "flow_id": flow_id,
        })
        url = f"{flow_url('api-keys')}?{params}"

        try:
            req = urllib.request.Request(
                url,
                headers=self._headers(),
                method="GET",
            )

            logger.info(f">>> GET {url}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"<<< {resp.status} OK")
            logger.debug(f"<<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            items = body.get("items", [])
            total = body.get("total", len(items))

            return ApiResponse(
                success=True,
                data=body,
                message="API keys fetched",
                total=total,
            )

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "get_api_keys")
        except urllib.error.URLError as e:
            logger.error(f"<<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to server")
        except Exception as e:
            logger.error(f"<<< get_api_keys exception: {e}")
            return ApiResponse(success=False, message=str(e))

    # ── Delete API Key ────────────────────────────────────────────────

    def delete_api_key(self, api_key_id: int) -> ApiResponse:
        """
        DELETE /api-keys/{api_key_id} — Delete an api-key/cookie by ID.

        Returns:
            ApiResponse with success=True if deleted.
        """
        url = flow_url(f"api-keys/{api_key_id}")

        try:
            req = urllib.request.Request(
                url,
                headers=self._headers(),
                method="DELETE",
            )

            logger.info(f">>> DELETE {url}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"<<< {resp.status} OK")
            logger.debug(f"<<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            ok = body.get("ok", False)
            return ApiResponse(success=ok, data=body, message="API key deleted" if ok else "Delete failed")

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "delete_api_key")
        except urllib.error.URLError as e:
            logger.error(f"<<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to server")
        except Exception as e:
            logger.error(f"<<< delete_api_key exception: {e}")
            return ApiResponse(success=False, message=str(e))
    # ── Refresh / re-check a single api-key ────────────────────────────

    def refresh_api_key(self, api_key_id: int) -> ApiResponse:
        """
        PUT /api-keys/{api_key_id}/refresh — Re-test if a cookie/api-key is still alive.

        Returns:
            ApiResponse with updated status.
        """
        url = flow_url(f"api-keys/{api_key_id}/refresh")

        try:
            req = urllib.request.Request(
                url,
                headers=self._headers(),
                method="PUT",
                data=b"{}",
            )

            logger.info(f">>> PUT {url}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"<<< {resp.status} OK")
            logger.debug(f"<<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            return ApiResponse(success=True, data=body, message="Cookie refreshed")

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "refresh_api_key")
        except urllib.error.URLError as e:
            logger.error(f"<<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to server")
        except Exception as e:
            logger.error(f"<<< refresh_api_key exception: {e}")
            return ApiResponse(success=False, message=str(e))

    # ── Assign API-Key to Flow ────────────────────────────────────────

    def assign_api_key_to_flow(self, api_key_id: int, flow_id: int) -> ApiResponse:
        """
        PUT /api-keys/{api_key_id} — Assign an api-key/cookie to a flow.

        Args:
            api_key_id: ID of the api-key to update.
            flow_id: Flow ID to link to.

        Returns:
            ApiResponse with updated api-key data.
        """
        url = flow_url(f"api-keys/{api_key_id}")
        payload = json.dumps({"flow_id": flow_id}).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers=self._headers(with_content_type=True),
                method="PUT",
            )

            logger.info(f">>> PUT {url} (flow_id={flow_id})")
            logger.debug(f">>> Body: {json.dumps({'flow_id': flow_id})}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"<<< {resp.status} OK")
            logger.debug(f"<<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            return ApiResponse(success=True, data=body, message="API key assigned to flow")

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "assign_api_key_to_flow")
        except urllib.error.URLError as e:
            logger.error(f"<<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to server")
        except Exception as e:
            logger.error(f"<<< assign_api_key_to_flow exception: {e}")
            return ApiResponse(success=False, message=str(e))

    # ── Error Handling ────────────────────────────────────────────────

    def _handle_http_error(self, e: urllib.error.HTTPError, method: str) -> ApiResponse:
        """Parse HTTP error responses consistently."""
        try:
            error_data = e.read().decode("utf-8")
            error_body = json.loads(error_data)
            error_msg = error_body.get("message", f"HTTP {e.code}")
        except Exception:
            error_data = ""
            error_msg = f"HTTP {e.code}"
        logger.error(f"<<< {e.code} Error in {method}")
        logger.debug(f"<<< Response: {error_data}")
        return ApiResponse(success=False, message=error_msg)
