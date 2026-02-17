"""
Whisk Desktop — Mock API Resource Operations.

Mixin class providing cookie, project, token, flow, and API key management.
"""
import random
import uuid
from datetime import datetime, timedelta

from app.api.models import (
    ApiResponse, CookieItem, ProjectItem, TokenItem,
    FlowItem, FlowConfig, ApiKeyItem,
)


class ResourceOpsMixin:
    """Mixin providing resource management (cookies, projects, tokens, flows, api-keys)."""

    # --- Cookie Management ---

    def get_cookies(self) -> ApiResponse:
        """Get all stored cookies."""
        return ApiResponse(
            success=True,
            data=[c.to_dict() for c in self._cookies],
            total=len(self._cookies),
        )

    def add_cookie(self, data: dict) -> ApiResponse:
        """Add a new cookie."""
        cookie = CookieItem(
            id=str(uuid.uuid4()),
            name=data.get("name", ""),
            value=data.get("value", ""),
            domain=data.get("domain", ""),
            status="unknown",
            expires_at=None,
            added_at=datetime.now(),
        )
        self._cookies.append(cookie)
        return ApiResponse(
            success=True,
            data=cookie.to_dict(),
            message="Cookie added",
        )

    def delete_cookie(self, cookie_id: str) -> ApiResponse:
        """Delete a cookie by ID."""
        before = len(self._cookies)
        self._cookies = [c for c in self._cookies if c.id != cookie_id]
        if len(self._cookies) < before:
            return ApiResponse(success=True, message="Cookie deleted")
        return ApiResponse(success=False, message="Cookie not found")

    def refresh_cookies(self) -> ApiResponse:
        """Refresh all cookie statuses (mock: randomly assign)."""
        for cookie in self._cookies:
            if cookie.is_expired:
                cookie.status = "expired"
            elif cookie.expires_at:
                cookie.status = "valid"
            else:
                cookie.status = random.choice(["valid", "unknown"])
        return ApiResponse(
            success=True,
            data=[c.to_dict() for c in self._cookies],
            total=len(self._cookies),
            message="Cookies refreshed",
        )

    def check_cookie(self, cookie_id: str) -> ApiResponse:
        """Check validity of a single cookie."""
        for cookie in self._cookies:
            if cookie.id == cookie_id:
                if cookie.is_expired:
                    cookie.status = "expired"
                elif cookie.expires_at:
                    cookie.status = "valid"
                else:
                    cookie.status = random.choice(["valid", "unknown"])
                return ApiResponse(success=True, data=cookie.to_dict())
        return ApiResponse(success=False, message="Cookie not found")

    # --- Project Management ---

    def get_projects(self) -> ApiResponse:
        """Get all projects."""
        return ApiResponse(
            success=True,
            data=[p.to_dict() for p in self._projects],
            total=len(self._projects),
        )

    def add_project(self, data: dict) -> ApiResponse:
        """Create a new project."""
        project = ProjectItem(
            id=str(uuid.uuid4()),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self._projects.append(project)
        return ApiResponse(
            success=True,
            data=project.to_dict(),
            message="Project created",
        )

    def update_project(self, project_id: str, data: dict) -> ApiResponse:
        """Update an existing project."""
        for project in self._projects:
            if project.id == project_id:
                for key in ("name", "description", "status"):
                    if key in data:
                        setattr(project, key, data[key])
                project.updated_at = datetime.now()
                return ApiResponse(success=True, data=project.to_dict(),
                                   message="Project updated")
        return ApiResponse(success=False, message="Project not found")

    def delete_project(self, project_id: str) -> ApiResponse:
        """Delete a project by ID."""
        before = len(self._projects)
        self._projects = [p for p in self._projects if p.id != project_id]
        if len(self._projects) < before:
            if self._active_project_id == project_id:
                self._active_project_id = self._projects[0].id if self._projects else ""
            return ApiResponse(success=True, message="Project deleted")
        return ApiResponse(success=False, message="Project not found")

    def set_active_project(self, project_id: str) -> ApiResponse:
        """Set the active project."""
        for project in self._projects:
            if project.id == project_id:
                self._active_project_id = project_id
                return ApiResponse(success=True, data=project.to_dict(),
                                   message="Active project set")
        return ApiResponse(success=False, message="Project not found")

    def get_active_project(self) -> ApiResponse:
        """Get the currently active project."""
        for project in self._projects:
            if project.id == self._active_project_id:
                return ApiResponse(success=True, data=project.to_dict())
        return ApiResponse(success=True, data=None)

    # --- Token Management ---

    def get_tokens(self) -> ApiResponse:
        """Get all tokens."""
        # Auto-update expired statuses
        for token in self._tokens:
            if token.is_expired and token.status == "active":
                token.status = "expired"
        return ApiResponse(
            success=True,
            data=[t.to_dict() for t in self._tokens],
            total=len(self._tokens),
        )

    def add_token(self, data: dict) -> ApiResponse:
        """Create a new token."""
        expires_at = data.get("expires_at")
        if isinstance(expires_at, (int, float)):
            expires_at = datetime.now() + timedelta(days=expires_at)
        elif isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at)
            except ValueError:
                expires_at = None

        token = TokenItem(
            id=str(uuid.uuid4()),
            name=data.get("name", ""),
            value=data.get("value", ""),
            token_type=data.get("token_type", "bearer"),
            status="active",
            expires_at=expires_at,
            created_at=datetime.now(),
        )
        self._tokens.append(token)
        return ApiResponse(
            success=True,
            data=token.to_dict(),
            message="Token created",
        )

    def update_token(self, token_id: str, data: dict) -> ApiResponse:
        """Update an existing token."""
        for token in self._tokens:
            if token.id == token_id:
                for key in ("name", "value", "token_type", "status"):
                    if key in data:
                        setattr(token, key, data[key])
                if "expires_at" in data:
                    val = data["expires_at"]
                    if isinstance(val, (int, float)):
                        token.expires_at = datetime.now() + timedelta(days=val)
                    elif isinstance(val, str):
                        try:
                            token.expires_at = datetime.fromisoformat(val)
                        except ValueError:
                            pass
                    else:
                        token.expires_at = val
                return ApiResponse(success=True, data=token.to_dict(),
                                   message="Token updated")
        return ApiResponse(success=False, message="Token not found")

    def delete_token(self, token_id: str) -> ApiResponse:
        """Delete a token by ID."""
        before = len(self._tokens)
        self._tokens = [t for t in self._tokens if t.id != token_id]
        if len(self._tokens) < before:
            return ApiResponse(success=True, message="Token deleted")
        return ApiResponse(success=False, message="Token not found")

    # --- Flow Management ---

    def create_flow(self, data: dict) -> ApiResponse:
        """Create a new flow (mock)."""
        self._flow_id_counter += 1
        now = datetime.now()

        config_data = data.get("config", {})
        config = FlowConfig.from_dict(config_data) if isinstance(config_data, dict) else FlowConfig()

        flow = FlowItem(
            id=self._flow_id_counter,
            name=data.get("name", f"flow_{self._flow_id_counter}"),
            description=data.get("description", ""),
            type=data.get("type", "WHISK"),
            status=data.get("status", "pending"),
            config=config,
            key_code=data.get("key_code"),
            upload_count=0,
            user_id=0,
            created_at=now,
            updated_at=now,
        )
        self._flows.append(flow)
        return ApiResponse(
            success=True,
            data=flow.to_dict(),
            message="Flow created",
        )

    def get_flows(
        self, offset: int = 0, limit: int = 20,
        sort: str = "updated_at:desc", flow_type: str = "WHISK",
    ) -> ApiResponse:
        """Get flows list (mock) with pagination."""
        # Filter by type
        filtered = [f for f in self._flows if f.type == flow_type]

        # Sort
        if sort:
            parts = sort.split(":")
            sort_key = parts[0] if parts else "updated_at"
            descending = len(parts) > 1 and parts[1] == "desc"
            try:
                filtered.sort(key=lambda f: getattr(f, sort_key, ""), reverse=descending)
            except (AttributeError, TypeError):
                pass

        total = len(filtered)
        page = filtered[offset:offset + limit]
        has_more = (offset + limit) < total

        return ApiResponse(
            success=True,
            data={
                "items": [f.to_dict() for f in page],
                "total": total,
                "offset": offset,
                "limit": limit,
                "has_more": has_more,
            },
            total=total,
        )

    def delete_flow(self, flow_id: int) -> ApiResponse:
        """Delete a flow by ID (mock)."""
        before = len(self._flows)
        self._flows = [f for f in self._flows if f.id != flow_id]
        if len(self._flows) < before:
            return ApiResponse(success=True, data={"ok": True}, message="Flow deleted")
        return ApiResponse(success=False, message="Flow not found")

    # --- Cookie / API-Key Management (Server) ---

    def test_server_cookie(self, data: dict) -> ApiResponse:
        """Test cookie validity (mock: always returns ok)."""
        provider = data.get("provider", "WHISK")
        return ApiResponse(
            success=True,
            data={
                "ok": True,
                "msg_error": "",
                "status": "active",
                "response_time": 0.5,
                "provider_info": {
                    "provider": provider.lower(),
                    "token_match": True,
                    "user_email": "mock@example.com",
                    "user_name": "Mock User",
                    "expires": "2026-12-31T23:59:59.000Z",
                },
            },
            message="Cookie is valid",
        )

    def save_server_cookie(self, data: dict) -> ApiResponse:
        """Save/create a cookie as api-key (mock)."""
        self._api_key_id_counter += 1
        now = datetime.now()

        api_key = ApiKeyItem(
            id=self._api_key_id_counter,
            label=data.get("label", f"WHISK - mock - {now.isoformat()}"),
            value="ya29.mock_access_token_" + str(self._api_key_id_counter),
            provider=data.get("provider", "WHISK"),
            status="active",
            flow_id=data.get("flow_id"),
            user_id=0,
            metadata={
                "cookies": data.get("cookies", {}),
                "user_email": "mock@example.com",
                "user_name": "Mock User",
            },
            created_at=now,
        )
        self._api_keys.append(api_key)

        return ApiResponse(
            success=True,
            data={
                "status": "ok",
                "message": f"{api_key.provider} token saved successfully",
                "provider": api_key.provider,
                "api_key": api_key.to_dict(),
                "session": {
                    "access_token": api_key.value,
                    "expires": "2026-12-31T23:59:59.000Z",
                    "user": {
                        "email": "mock@example.com",
                        "name": "Mock User",
                    },
                },
            },
            message=f"{api_key.provider} token saved successfully",
        )

    def get_api_keys(
        self, flow_id: int, provider: str = "WHISK",
        offset: int = 0, limit: int = 1000,
        status: str = "ALL", mine: bool = True,
        sort: str = "updated_at:desc",
    ) -> ApiResponse:
        """Get api-keys list (mock) with pagination."""
        filtered = [
            k for k in self._api_keys
            if k.provider == provider and (k.flow_id == flow_id or flow_id is None)
        ]
        if status != "ALL":
            filtered = [k for k in filtered if k.status == status.lower()]

        total = len(filtered)
        page = filtered[offset:offset + limit]

        return ApiResponse(
            success=True,
            data={
                "items": [k.to_dict() for k in page],
                "total": total,
                "offset": offset,
                "limit": limit,
            },
            total=total,
        )

    def delete_api_key(self, api_key_id: int) -> ApiResponse:
        """Delete an api-key by ID (mock)."""
        before = len(self._api_keys)
        self._api_keys = [k for k in self._api_keys if k.id != api_key_id]
        if len(self._api_keys) < before:
            return ApiResponse(success=True, data={"ok": True}, message="API key deleted")
        return ApiResponse(success=False, message="API key not found")
