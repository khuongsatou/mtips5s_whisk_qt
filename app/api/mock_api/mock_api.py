"""
Whisk Desktop — Mock API Implementation.

In-memory queue API with sample data for development and testing.
Supports checkpoint persistence to JSON file.

The MockApi class composes functionality from three mixins:
- SampleDataMixin: sample data generators
- QueueOpsMixin: queue CRUD + execution + checkpoint persistence
- ResourceOpsMixin: cookie, project, token, flow, api-key management
"""
import os

from app.api.base_api import BaseApi
from app.api.models import TaskItem
from app.api.mock_api.sample_data import SampleDataMixin
from app.api.mock_api.queue_ops import QueueOpsMixin, CHECKPOINT_DIR
from app.api.mock_api.resource_ops import ResourceOpsMixin


class MockApi(SampleDataMixin, QueueOpsMixin, ResourceOpsMixin, BaseApi):
    """Mock API with in-memory image creation queue."""

    def __init__(self, flow_id: int | str | None = None):
        """Initialize mock API with sample queue data."""
        self._flow_id = str(flow_id) if flow_id else None
        # Per-project checkpoint file
        if self._flow_id:
            fname = f"queue_checkpoint_{self._flow_id}.json"
        else:
            fname = "queue_checkpoint.json"
        self._checkpoint_path = os.path.join(CHECKPOINT_DIR, fname)
        self._queue: list[TaskItem] = []
        self._cookies = self._generate_sample_cookies()
        self._projects = self._generate_sample_projects()
        self._tokens = self._generate_sample_tokens()
        self._active_project_id: str = self._projects[0].id if self._projects else ""
        self._flows = []
        self._flow_id_counter = 100
        self._api_keys = []
        self._api_key_id_counter = 4000
        self._is_running = False
        self._is_paused = False
        # Load checkpoint on startup
        self._load_checkpoint()
