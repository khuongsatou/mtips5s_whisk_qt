"""
Whisk Desktop — Abstract Base API.

Defines the interface for queue-based image creation operations.
"""
from abc import ABC, abstractmethod
from app.api.models import ApiResponse


class BaseApi(ABC):
    """Abstract base for all API implementations (mock & real)."""

    # --- Queue CRUD ---

    @abstractmethod
    def get_queue(self) -> ApiResponse:
        """Get all tasks in the queue."""

    @abstractmethod
    def get_task(self, task_id: str) -> ApiResponse:
        """Get a single task by ID."""

    @abstractmethod
    def add_to_queue(self, data: dict) -> ApiResponse:
        """Add a new task to the queue."""

    @abstractmethod
    def update_task(self, task_id: str, data: dict) -> ApiResponse:
        """Update an existing task."""

    @abstractmethod
    def delete_tasks(self, task_ids: list[str]) -> ApiResponse:
        """Delete one or more tasks from the queue."""

    @abstractmethod
    def clear_queue(self) -> ApiResponse:
        """Delete all tasks from the queue."""

    # --- Queue Execution ---

    @abstractmethod
    def run_selected(self, task_ids: list[str]) -> ApiResponse:
        """Start running selected tasks."""

    @abstractmethod
    def run_all(self) -> ApiResponse:
        """Start running all pending tasks."""

    @abstractmethod
    def pause(self) -> ApiResponse:
        """Pause execution."""

    @abstractmethod
    def stop(self) -> ApiResponse:
        """Stop execution."""

    @abstractmethod
    def retry_errors(self) -> ApiResponse:
        """Retry all tasks with error status."""

    # --- Cookie Management ---

    @abstractmethod
    def get_cookies(self) -> ApiResponse:
        """Get all stored cookies."""

    @abstractmethod
    def add_cookie(self, data: dict) -> ApiResponse:
        """Add a new cookie."""

    @abstractmethod
    def delete_cookie(self, cookie_id: str) -> ApiResponse:
        """Delete a cookie by ID."""

    @abstractmethod
    def refresh_cookies(self) -> ApiResponse:
        """Refresh/re-check all cookie statuses."""

    @abstractmethod
    def check_cookie(self, cookie_id: str) -> ApiResponse:
        """Check validity of a single cookie."""

    # --- Project Management ---

    @abstractmethod
    def get_projects(self) -> ApiResponse:
        """Get all projects."""

    @abstractmethod
    def add_project(self, data: dict) -> ApiResponse:
        """Create a new project."""

    @abstractmethod
    def update_project(self, project_id: str, data: dict) -> ApiResponse:
        """Update an existing project."""

    @abstractmethod
    def delete_project(self, project_id: str) -> ApiResponse:
        """Delete a project by ID."""

    @abstractmethod
    def set_active_project(self, project_id: str) -> ApiResponse:
        """Set the active project."""

    @abstractmethod
    def get_active_project(self) -> ApiResponse:
        """Get the currently active project."""

    # --- Token Management ---

    @abstractmethod
    def get_tokens(self) -> ApiResponse:
        """Get all tokens."""

    @abstractmethod
    def add_token(self, data: dict) -> ApiResponse:
        """Create a new token."""

    @abstractmethod
    def update_token(self, token_id: str, data: dict) -> ApiResponse:
        """Update an existing token."""

    @abstractmethod
    def delete_token(self, token_id: str) -> ApiResponse:
        """Delete a token by ID."""

    # --- Flow Management ---

    @abstractmethod
    def create_flow(self, data: dict) -> ApiResponse:
        """Create a new flow on the server."""

    @abstractmethod
    def get_flows(
        self, offset: int = 0, limit: int = 20,
        sort: str = "updated_at:desc", flow_type: str = "WHISK",
    ) -> ApiResponse:
        """Get flows list from the server with pagination."""

    @abstractmethod
    def delete_flow(self, flow_id: int) -> ApiResponse:
        """Delete a flow by ID."""

    # --- Cookie / API-Key Management (Server) ---

    @abstractmethod
    def test_server_cookie(self, data: dict) -> ApiResponse:
        """Test cookie validity against the server."""

    @abstractmethod
    def save_server_cookie(self, data: dict) -> ApiResponse:
        """Save/create a cookie as api-key on the server."""

    @abstractmethod
    def get_api_keys(
        self, flow_id: int, provider: str = "WHISK",
        offset: int = 0, limit: int = 1000,
        status: str = "ALL", mine: bool = True,
        sort: str = "updated_at:desc",
    ) -> ApiResponse:
        """Get api-keys/cookies list from the server."""

    @abstractmethod
    def delete_api_key(self, api_key_id: int) -> ApiResponse:
        """Delete an api-key/cookie by ID."""


