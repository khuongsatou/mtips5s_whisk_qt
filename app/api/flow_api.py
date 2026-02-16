"""
Whisk Desktop — Flow API Client.

Real HTTP client for flow management endpoints (create, list).
Uses Bearer token authentication from AuthManager.
"""
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from app.api.api_config import flow_url
from app.api.models import ApiResponse

logger = logging.getLogger("whisk.flow_api")


class FlowApiClient:
    """HTTP client for flow CRUD operations against the flow server."""

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

    # ── Create Flow ───────────────────────────────────────────────────

    def create_flow(self, data: dict) -> ApiResponse:
        """
        POST /flows — Create a new flow.

        Args:
            data: Flow creation payload. Must include at least 'name'.
                  If 'type' is not provided, defaults to 'WHISK'.

        Returns:
            ApiResponse with the created flow data on success.
        """
        # Ensure type is WHISK
        if "type" not in data:
            data["type"] = "WHISK"

        url = flow_url("flows")
        payload = json.dumps(data).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers=self._headers(with_content_type=True),
                method="POST",
            )

            logger.info(f"📤 >>> POST {url}")
            logger.debug(f"📤 >>> Body: {json.dumps(data, indent=2, ensure_ascii=False)}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"📥 <<< {resp.status} OK")
            logger.debug(f"📥 <<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            return ApiResponse(success=True, data=body, message="Flow created")

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "create_flow")
        except urllib.error.URLError as e:
            logger.error(f"❌ <<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to flow server")
        except Exception as e:
            logger.error(f"❌ <<< create_flow exception: {e}")
            return ApiResponse(success=False, message=str(e))

    # ── List Flows ────────────────────────────────────────────────────

    def get_flows(
        self,
        offset: int = 0,
        limit: int = 20,
        sort: str = "updated_at:desc",
        flow_type: str = "WHISK",
    ) -> ApiResponse:
        """
        GET /flows?offset=&limit=&sort=&type= — List flows with pagination.

        Returns:
            ApiResponse with data = {items: [...], total, offset, limit, has_more}.
        """
        params = urllib.parse.urlencode({
            "offset": offset,
            "limit": limit,
            "sort": sort,
            "type": flow_type,
        })
        url = f"{flow_url('flows')}?{params}"

        try:
            req = urllib.request.Request(
                url,
                headers=self._headers(),
                method="GET",
            )

            logger.info(f"📤 >>> GET {url}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"📥 <<< {resp.status} OK")
            logger.debug(f"📥 <<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            items = body.get("items", [])
            total = body.get("total", len(items))

            return ApiResponse(
                success=True,
                data=body,
                message="Flows fetched",
                total=total,
            )

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "get_flows")
        except urllib.error.URLError as e:
            logger.error(f"❌ <<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to flow server")
        except Exception as e:
            logger.error(f"❌ <<< get_flows exception: {e}")
            return ApiResponse(success=False, message=str(e))

    # ── Delete Flow ──────────────────────────────────────────────────

    def delete_flow(self, flow_id: int) -> ApiResponse:
        """
        DELETE /flows/{flow_id} — Delete a flow by ID.

        Returns:
            ApiResponse with success=True if deleted.
        """
        url = flow_url(f"flows/{flow_id}")

        try:
            req = urllib.request.Request(
                url,
                headers=self._headers(),
                method="DELETE",
            )

            logger.info(f"📤 >>> DELETE {url}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"📥 <<< {resp.status} OK")
            logger.debug(f"📥 <<< Response: {json.dumps(body, indent=2, ensure_ascii=False)}")

            ok = body.get("ok", False)
            return ApiResponse(success=ok, data=body, message="Flow deleted" if ok else "Delete failed")

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "delete_flow")
        except urllib.error.URLError as e:
            logger.error(f"❌ <<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to flow server")
        except Exception as e:
            logger.error(f"❌ <<< delete_flow exception: {e}")
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
        logger.error(f"❌ <<< {e.code} Error in {method}")
        logger.debug(f"📥 <<< Response: {error_data}")
        return ApiResponse(success=False, message=error_msg)
