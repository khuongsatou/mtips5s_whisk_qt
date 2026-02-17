"""
Whisk Desktop — Image Creator Page.

Full-featured page: left config panel, right table + toolbar.
Background worker generates images via WorkflowApiClient and saves to disk.

The ImageCreatorPage class composes functionality from:
- PageHandlersMixin: queue ops, workflow, generation, downloads, auth
Worker classes (GenerationWorker, _RefUploadWorker) live in workers.py.
"""
import logging
import time

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
)
from PySide6.QtCore import Qt, QTimer, Signal
from app.widgets.config_panel import ConfigPanel
from app.widgets.task_queue_table import TaskQueueTable
from app.widgets.queue_toolbar import QueueToolbar
from app.widgets.log_panel import LogPanel
from app.widgets.toast_notification import ToastNotification
from app.pages.image_creator_page.page_handlers import PageHandlersMixin
from app.pages.image_creator_page.workers import GenerationWorker

logger = logging.getLogger("whisk.image_creator")


class ImageCreatorPage(PageHandlersMixin, QWidget):
    """Main image creator page with config panel, queue table, and toolbar."""

    queue_data_changed = Signal()  # Emitted when queue data is refreshed

    MAX_RETRIES = 2  # Max retry attempts (3 total = 1 original + 2 retries)

    def __init__(self, translator, api, parent=None,
                 workflow_api=None, cookie_api=None, active_flow_id=None,
                 flow_name: str = ""):
        super().__init__(parent)
        self.translator = translator
        self.api = api
        self.workflow_api = workflow_api
        self.cookie_api = cookie_api
        self._active_flow_id = active_flow_id
        self._flow_name: str = flow_name  # Project/flow name (e.g., "accc")
        self._workflow_id: str = ""  # Set during workflow creation or loaded from server
        self._workflow_name: str = ""  # Workflow name from Labs (e.g., "Whisk: 2/16/26")
        self.translator.language_changed.connect(self.retranslate)
        self._selected_ids: list[str] = []
        self._is_generating = False
        self._worker: GenerationWorker | None = None
        self._running_task_ids: set[str] = set()
        self._local_progress: dict[str, int] = {}  # tid → estimated %
        self._upload_status: dict[str, str] = {}  # tid → upload status text
        self._task_start_times: dict[str, float] = {}  # tid → time.time()
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(500)  # tick every 500ms
        self._progress_timer.timeout.connect(self._tick_progress)

        # Auto-retry state
        self._retry_counts: dict[str, int] = {}  # task_id → attempt count
        self._auto_retry_timer = QTimer(self)
        self._auto_retry_timer.setSingleShot(True)
        self._auto_retry_timer.setInterval(60_000)  # 60 seconds
        self._auto_retry_timer.timeout.connect(self._do_auto_retry)

        self._setup_ui()
        self._connect_signals()
        # Restore persisted workflow if flow_id is known
        if self._active_flow_id:
            self._load_workflow(self._active_flow_id)
        self.refresh_data()

    def set_active_flow_id(self, flow_id):
        """Update the active flow ID (called when project changes)."""
        self._active_flow_id = int(flow_id) if flow_id else None
        # Restore persisted workflow for this flow
        if self._active_flow_id:
            self._load_workflow(self._active_flow_id)

    def _setup_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setObjectName("main_splitter")

        # Left: Config panel
        self._config = ConfigPanel(self.translator)
        self._config.setMinimumWidth(180)
        self._config.setMaximumWidth(700)
        self._splitter.addWidget(self._config)

        # Right: Table + Toolbar
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._table = TaskQueueTable(self.translator)
        right_layout.addWidget(self._table, 1)

        self._toolbar = QueueToolbar(self.translator)
        right_layout.addWidget(self._toolbar)

        # Log panel at bottom
        self._log_panel = LogPanel()
        right_layout.addWidget(self._log_panel)

        self._splitter.addWidget(right_widget)

        # Toast notification (overlays on top of right panel)
        self._toast = ToastNotification(right_widget)
        right_widget.setMinimumWidth(200)

        # Initial sizes: ~400px config, rest for table
        self._splitter.setSizes([400, 800])
        self._splitter.setStretchFactor(0, 0)  # Config: fixed size
        self._splitter.setStretchFactor(1, 1)   # Table: stretch to fill

        outer.addWidget(self._splitter)

    def _connect_signals(self):
        """Wire config panel, table, and toolbar signals."""
        # Config → add to queue
        self._config.add_to_queue.connect(self._on_add_to_queue)
        self._config.ref_images_picked.connect(self._on_ref_images_picked)
        self._config.workflow_requested.connect(self._on_workflow_requested)
        self._config.request_upload_ref.connect(self._on_request_upload_ref)

        # Table selection
        self._table.task_selected.connect(self._on_selection_changed)

        # Toolbar actions
        self._toolbar.add_row.connect(self._on_add_row)
        self._toolbar.delete_selected.connect(self._on_delete_selected)
        self._toolbar.delete_all.connect(self._on_delete_all)
        self._toolbar.retry_errors.connect(self._on_retry_errors)
        self._toolbar.run_selected.connect(self._on_run_selected)
        self._toolbar.run_all.connect(self._on_run_all)
        self._toolbar.clear_checkpoint.connect(self._on_clear_checkpoint)
        self._toolbar.download_all.connect(self._on_download_all)
        self._toolbar.select_errors.connect(self._table.select_errors)

        # Pagination
        self._toolbar.prev_page.connect(self._table.prev_page)
        self._toolbar.next_page.connect(self._table.next_page)
        self._table.page_changed.connect(self._toolbar.update_page_info)
        self._table.stats_changed.connect(self._toolbar.update_stats)

        # Search
        self._toolbar.search_changed.connect(self._table.set_search_filter)
        self._toolbar.status_filter_changed.connect(self._table.set_status_filter)

        # Table download + open folder
        self._table.download_clicked.connect(self._on_download)
        self._table.open_folder_clicked.connect(self._on_open_folder)

        # Table prompt editing
        self._table.prompt_edited.connect(self._on_prompt_edited)

    def refresh_data(self):
        """Reload the queue from API."""
        response = self.api.get_queue()
        if response.success:
            tasks = response.data or []
            # Cleanup stuck tasks: if not generating, any "creating"/"running"
            # tasks are leftovers from interrupted runs — mark as error
            if not self._is_generating:
                for t in tasks:
                    if t.get("status") in ("creating", "running"):
                        t["status"] = "error"
                        t["error_message"] = (
                            "Task bị gián đoạn. Hãy thử lại hoặc đổi prompt khác."
                        )
                        self.api.update_task(t["id"], {
                            "status": "error",
                            "error_message": t["error_message"],
                        })
                        logger.info(f"🔧 Fixed stuck task {t['id'][:8]}... → error")
            self._table.load_data(tasks)
            self.queue_data_changed.emit()
