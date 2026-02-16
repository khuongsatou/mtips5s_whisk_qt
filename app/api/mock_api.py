"""
Whisk Desktop — Mock API Implementation.

In-memory queue API with sample data for development and testing.
Supports checkpoint persistence to JSON file.
"""
import json
import logging
import os
import uuid
import random
from datetime import datetime, timedelta
from app.api.base_api import BaseApi
from app.api.models import ApiResponse, TaskItem, CookieItem, ProjectItem, TokenItem, FlowItem, FlowConfig, ApiKeyItem

logger = logging.getLogger("whisk.mock_api")

CHECKPOINT_DIR = os.path.join(os.path.expanduser("~"), ".whisk_pro")
CHECKPOINT_PATH = os.path.join(CHECKPOINT_DIR, "queue_checkpoint.json")


class MockApi(BaseApi):
    """Mock API with in-memory image creation queue."""

    SAMPLE_PROMPTS = [
        "+Herring Gull (Larus argentatus), pale yellow eye, winter-streaked gray-brown lines on white head/neck",
        "+Herring Gull (Larus argentatus), pale yellow eye, winter-streaked head/neck, yellow bill with red spot",
        "+Herring Gull (Larus argentatus), same identifying features (pale yellow eye; winter streaks; yellow bill)",
        "+Golden Eagle soaring over mountain ridge, wingspan fully extended, dramatic cloudy sky background",
        "+Red Fox (Vulpes vulpes) in autumn forest, bushy tail, alert posture, golden-orange fur",
        "+Atlantic Puffin on coastal cliff, colorful beak, black and white plumage, ocean background",
        "+Snow Leopard in Himalayan landscape, spotted grey coat, long bushy tail, rocky terrain",
        "+Monarch Butterfly on purple coneflower, orange and black wings spread, macro photography",
        "+Blue Whale surfacing, massive body emerging from deep blue ocean, water spray from blowhole",
        "+Japanese Macaque in hot spring, snow on head, steam rising, winter forest background",
    ]

    MODELS = ["Nano Banana Pro", "Flux Standard", "SDXL Ultra"]
    RATIOS = ["16:9", "9:16", "1:1", "4:3"]
    QUALITIES = ["1K", "2K", "4K"]

    def __init__(self):
        """Initialize mock API with sample queue data."""
        self._queue: list[TaskItem] = []
        self._cookies: list[CookieItem] = self._generate_sample_cookies()
        self._projects: list[ProjectItem] = self._generate_sample_projects()
        self._tokens: list[TokenItem] = self._generate_sample_tokens()
        self._active_project_id: str = self._projects[0].id if self._projects else ""
        self._flows: list[FlowItem] = []
        self._flow_id_counter = 100
        self._api_keys: list[ApiKeyItem] = []
        self._api_key_id_counter = 4000
        self._is_running = False
        self._is_paused = False
        # Load checkpoint on startup
        self._load_checkpoint()

    def _generate_sample_tokens(self) -> list[TokenItem]:
        """Generate sample tokens for development."""
        import string
        now = datetime.now()
        return [
            TokenItem(
                id=str(uuid.uuid4()),
                name="Whisk API Key",
                value="whsk_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=32)),
                token_type="api_key",
                status="active",
                expires_at=now + timedelta(days=30),
                created_at=now - timedelta(days=5),
            ),
            TokenItem(
                id=str(uuid.uuid4()),
                name="Google OAuth Token",
                value="ya29." + ''.join(random.choices(string.ascii_letters + string.digits, k=40)),
                token_type="oauth",
                status="expired",
                expires_at=now - timedelta(hours=2),
                created_at=now - timedelta(days=10),
            ),
            TokenItem(
                id=str(uuid.uuid4()),
                name="Bearer Access Token",
                value="eyJhbGciOiJSUzI1NiIs..." + ''.join(random.choices(string.ascii_letters, k=20)),
                token_type="bearer",
                status="active",
                expires_at=now + timedelta(days=7),
                created_at=now - timedelta(days=1),
            ),
        ]

    def _generate_sample_projects(self) -> list[ProjectItem]:
        """Generate sample projects for development."""
        now = datetime.now()
        samples = [
            ("Bird Photography Collection", "High-quality bird images for nature magazine"),
            ("Product Marketing Assets", "E-commerce product photos with white background"),
            ("Fantasy Art Series", "Digital fantasy landscapes and character art"),
        ]
        projects = []
        for i, (name, desc) in enumerate(samples):
            projects.append(ProjectItem(
                id=str(uuid.uuid4()),
                name=name,
                description=desc,
                status="active" if i < 2 else "archived",
                created_at=now - timedelta(days=random.randint(1, 30)),
                updated_at=now - timedelta(hours=random.randint(1, 48)),
            ))
        return projects

    def _generate_sample_cookies(self) -> list[CookieItem]:
        """Generate sample cookies for development."""
        import string
        now = datetime.now()

        def _rand_name():
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            return f"cookie_{suffix}"

        return [
            CookieItem(
                id=str(uuid.uuid4()),
                name=_rand_name(),
                value="abc123def456ghi789jkl012mno345pqr678...",
                domain="labs.google",
                status="valid",
                expires_at=now + timedelta(days=7),
                added_at=now - timedelta(hours=2),
            ),
            CookieItem(
                id=str(uuid.uuid4()),
                name=_rand_name(),
                value="xyz789ghi012mno345pqr678stu901vwx234...",
                domain="labs.google",
                status="expired",
                expires_at=now - timedelta(hours=1),
                added_at=now - timedelta(days=3),
            ),
            CookieItem(
                id=str(uuid.uuid4()),
                name=_rand_name(),
                value="mno345pqr678stu901vwx234yza567bcd890...",
                domain="labs.google",
                status="unknown",
                expires_at=None,
                added_at=now - timedelta(days=1),
            ),
        ]

    def _generate_sample_queue(self) -> list[TaskItem]:
        """Generate 5 sample tasks matching the reference screenshot."""
        tasks = []
        now = datetime.now()
        statuses = ["completed", "completed", "completed", "completed", "running"]

        for i in range(5):
            status = statuses[i] if i < len(statuses) else "pending"
            task = TaskItem(
                id=str(uuid.uuid4()),
                stt=i + 1,
                task_name="Task 1",
                model="IMAGEN_3_5",
                aspect_ratio="16:9",
                quality="1K",
                reference_images=[],
                prompt=self.SAMPLE_PROMPTS[i % len(self.SAMPLE_PROMPTS)],
                output_images=[],
                status=status,
                elapsed_seconds=random.randint(8, 25) if status != "pending" else 0,
                error_message="",
                created_at=now - timedelta(minutes=random.randint(0, 60)),
            )
            tasks.append(task)
        return tasks

    # --- Checkpoint Persistence ---

    def _save_checkpoint(self):
        """Save current queue state to JSON checkpoint file."""
        try:
            os.makedirs(CHECKPOINT_DIR, exist_ok=True)
            data = [t.to_dict() for t in self._queue]
            # Convert datetime objects to ISO strings for JSON serialization
            for item in data:
                if "created_at" in item and hasattr(item["created_at"], "isoformat"):
                    item["created_at"] = item["created_at"].isoformat()
            with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}")

    def _load_checkpoint(self):
        """Load queue state from JSON checkpoint file on startup."""
        if not os.path.isfile(CHECKPOINT_PATH):
            return
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return
            self._queue = [TaskItem.from_dict(item) for item in data]
            logger.info(f"📂 Loaded {len(self._queue)} tasks from checkpoint")
        except Exception as e:
            logger.error(f"❌ Failed to load checkpoint: {e}")

    def clear_checkpoint(self) -> ApiResponse:
        """Delete the checkpoint file and clear the queue."""
        self._queue.clear()
        try:
            if os.path.isfile(CHECKPOINT_PATH):
                os.remove(CHECKPOINT_PATH)
                logger.info("🗑️ Checkpoint file deleted")
        except Exception as e:
            logger.error(f"❌ Failed to delete checkpoint: {e}")
        return ApiResponse(success=True, message="Checkpoint cleared")

    # --- Queue CRUD ---

    def get_queue(self) -> ApiResponse:
        """Get all tasks in the queue."""
        return ApiResponse(
            success=True,
            data=[t.to_dict() for t in self._queue],
            total=len(self._queue),
        )

    def get_task(self, task_id: str) -> ApiResponse:
        """Get a single task by ID."""
        for task in self._queue:
            if task.id == task_id:
                return ApiResponse(success=True, data=task.to_dict())
        return ApiResponse(success=False, message="Task not found")

    def add_to_queue(self, data: dict) -> ApiResponse:
        """Add a new task to the queue."""
        next_stt = max((t.stt for t in self._queue), default=0) + 1
        task = TaskItem(
            id=str(uuid.uuid4()),
            stt=next_stt,
            task_name=data.get("task_name", f"Task {next_stt}"),
            model=data.get("model", "IMAGEN_3_5"),
            aspect_ratio=data.get("aspect_ratio", "16:9"),
            quality=data.get("quality", "1K"),
            reference_images=data.get("reference_images", []),
            reference_images_by_cat=data.get("reference_images_by_cat", {"title": [], "scene": [], "style": []}),
            prompt=data.get("prompt", ""),
            images_per_prompt=data.get("images_per_prompt", 1),
            output_images=[],
            status="pending",
            elapsed_seconds=0,
            error_message="",
            output_folder=data.get("output_folder", ""),
            filename_prefix=data.get("filename_prefix", ""),
            created_at=datetime.now(),
        )
        self._queue.append(task)
        self._save_checkpoint()
        return ApiResponse(
            success=True,
            data=task.to_dict(),
            message="Task added to queue",
        )

    def update_task(self, task_id: str, data: dict) -> ApiResponse:
        """Update an existing task."""
        for task in self._queue:
            if task.id == task_id:
                for key in ("task_name", "model", "aspect_ratio", "quality",
                            "reference_images", "reference_images_by_cat",
                            "prompt", "images_per_prompt", "output_images",
                            "status", "progress", "elapsed_seconds", "error_message",
                            "output_folder", "filename_prefix"):
                    if key in data:
                        setattr(task, key, data[key])
                self._save_checkpoint()
                return ApiResponse(success=True, data=task.to_dict(),
                                   message="Task updated")
        return ApiResponse(success=False, message="Task not found")

    def delete_tasks(self, task_ids: list[str]) -> ApiResponse:
        """Delete tasks by IDs."""
        before = len(self._queue)
        self._queue = [t for t in self._queue if t.id not in task_ids]
        deleted = before - len(self._queue)
        # Re-number STT
        for i, task in enumerate(self._queue):
            task.stt = i + 1
        self._save_checkpoint()
        return ApiResponse(
            success=True,
            message=f"Deleted {deleted} task(s)",
        )

    def clear_queue(self) -> ApiResponse:
        """Delete all tasks."""
        count = len(self._queue)
        self._queue.clear()
        self._save_checkpoint()
        return ApiResponse(success=True, message=f"Cleared {count} task(s)")

    # --- Queue Execution ---

    def run_selected(self, task_ids: list[str]) -> ApiResponse:
        """Mark selected tasks as running (mock)."""
        started = 0
        for task in self._queue:
            if task.id in task_ids and task.status == "pending":
                task.status = "running"
                task.elapsed_seconds = 0
                started += 1
        self._is_running = True
        self._is_paused = False
        return ApiResponse(success=True, message=f"Started {started} task(s)")

    def run_all(self) -> ApiResponse:
        """Mark all pending tasks as running (mock)."""
        started = 0
        for task in self._queue:
            if task.status == "pending":
                task.status = "running"
                task.elapsed_seconds = 0
                started += 1
        self._is_running = True
        self._is_paused = False
        return ApiResponse(success=True, message=f"Started {started} task(s)")

    def pause(self) -> ApiResponse:
        """Pause execution (mock)."""
        self._is_paused = True
        return ApiResponse(success=True, message="Queue paused")

    def stop(self) -> ApiResponse:
        """Stop execution and reset running tasks to pending (mock)."""
        stopped = 0
        for task in self._queue:
            if task.status == "running":
                task.status = "pending"
                task.elapsed_seconds = 0
                stopped += 1
        self._is_running = False
        self._is_paused = False
        return ApiResponse(success=True, message=f"Stopped {stopped} task(s)")

    def retry_errors(self) -> ApiResponse:
        """Reset error tasks to pending (mock)."""
        retried = 0
        for task in self._queue:
            if task.status == "error":
                task.status = "pending"
                task.elapsed_seconds = 0
                task.error_message = ""
                retried += 1
        return ApiResponse(success=True, message=f"Retrying {retried} task(s)")

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
