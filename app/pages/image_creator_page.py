"""
Whisk Desktop — Image Creator Page.

Full-featured page: left config panel, right table + toolbar.
Background worker generates images via WorkflowApiClient and saves to disk.
"""
import base64
import logging
import os
import shutil
import time
import random
from app.prompt_normalizer import PromptNormalizer
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QFileDialog,
)
from PySide6.QtCore import Qt, QThread, Signal as QSignal, QTimer, QSettings
from app.widgets.config_panel import ConfigPanel
from app.widgets.task_queue_table import TaskQueueTable
from app.widgets.queue_toolbar import QueueToolbar
from app.widgets.log_panel import LogPanel
from app.widgets.styled_message_box import StyledMessageBox
from app.widgets.toast_notification import ToastNotification

logger = logging.getLogger("whisk.image_creator")


# ── Background worker for image generation ───────────────────────────


class GenerationWorker(QThread):
    """Runs image generation API calls in background threads with concurrency."""

    # (task_id, progress_pct, status, extra_data)
    task_progress = QSignal(str, int, str, dict)
    finished_all = QSignal()

    def __init__(
        self,
        workflow_api,
        google_token: str,
        workflow_id: str,
        tasks: list,
        concurrency: int = 2,
        workflow_name: str = "",
        flow_name: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.workflow_api = workflow_api
        self.google_token = google_token
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.flow_name = flow_name
        self.tasks = tasks
        self.concurrency = max(1, concurrency)
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    TASK_TIMEOUT = 120  # 2 minutes per task

    def run(self):
        logger.info(f"🏃 Worker starting with concurrency={self.concurrency} for {len(self.tasks)} tasks")
        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = {
                pool.submit(self._process_task, task): task
                for task in self.tasks
            }
            for future in as_completed(futures):
                if self._stop_flag:
                    break
                task = futures[future]
                task_id = task.get("id", "")
                try:
                    future.result()
                except Exception as exc:
                    # Catch any unhandled exceptions from _process_task
                    logger.error(f"❌ Task {task_id} unexpected error: {exc}")
        self.finished_all.emit()

    def _process_task(self, task: dict):
        """Process a single task (runs in a thread pool thread)."""
        if self._stop_flag:
            return

        task_id = task.get("id", "")
        prompt = task.get("prompt", "")
        aspect_ratio = task.get("aspect_ratio", "16:9")
        images_per_prompt = task.get("images_per_prompt", 1)
        output_folder = task.get("output_folder", "")
        filename_prefix = task.get("filename_prefix", "")

        # Mark as running with initial progress 10-15%
        initial_pct = random.randint(10, 15)
        self.task_progress.emit(task_id, initial_pct, "running", {})

        start_time = time.time()

        try:
            saved_paths = []
            for img_idx in range(images_per_prompt):
                if self._stop_flag:
                    break

                # Check timeout before making API call
                elapsed = time.time() - start_time
                if elapsed >= self.TASK_TIMEOUT:
                    raise TimeoutError(
                        f"Task timeout ({self.TASK_TIMEOUT}s). "
                        "Hãy thử đổi prompt khác / Try a different prompt."
                    )

                gen_resp = self.workflow_api.generate_image(
                    google_access_token=self.google_token,
                    workflow_id=self.workflow_id,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )

                if not gen_resp.success:
                    error_msg = gen_resp.message or "Generation failed"
                    # Check if it's a server-side timeout/creating stuck
                    if any(kw in error_msg.lower() for kw in ["timeout", "creating", "timed out"]):
                        raise TimeoutError(
                            f"{error_msg}. "
                            "Hãy thử đổi prompt khác / Try a different prompt."
                        )
                    raise Exception(error_msg)

                # Save image to file
                encoded_image = gen_resp.data.get("encoded_image", "")
                if encoded_image:
                    # Default: ~/Downloads/whisk_pro/project_name/
                    if not output_folder:
                        base = os.path.join(
                            os.path.expanduser("~"), "Downloads", "whisk_pro"
                        )
                        if self.workflow_name:
                            # Sanitize project name for filesystem
                            safe_wf = self.workflow_name.replace("/", "_").replace(":", "_").strip()
                            if self.flow_name:
                                safe_flow = self.flow_name.replace("/", "_").replace(":", "_").strip()
                                folder_name = f"{safe_flow}_{safe_wf}"
                            else:
                                folder_name = safe_wf
                            save_folder = os.path.join(base, folder_name)
                        elif self.flow_name:
                            safe_flow = self.flow_name.replace("/", "_").replace(":", "_").strip()
                            save_folder = os.path.join(base, safe_flow)
                        else:
                            save_folder = base
                    else:
                        save_folder = output_folder
                    saved_path = self._save_image(
                        encoded_image, save_folder,
                        filename_prefix, task.get("stt", 0), img_idx,
                    )
                    saved_paths.append(saved_path)
                    logger.info(f"💾 Image saved: {saved_path}")

            elapsed = int(time.time() - start_time)
            self.task_progress.emit(task_id, 100, "completed", {
                "elapsed_seconds": elapsed,
                "output_images": saved_paths,
            })

        except Exception as e:
            elapsed = int(time.time() - start_time)
            logger.error(f"❌ Task {task_id} failed: {e}")
            self.task_progress.emit(task_id, 0, "error", {
                "elapsed_seconds": elapsed,
                "error_message": str(e),
            })

    @staticmethod
    def _save_image(
        encoded_image: str,
        output_folder: str,
        prefix: str,
        stt: int,
        img_idx: int,
    ) -> str:
        """Save base64 encoded image to output folder."""
        os.makedirs(output_folder, exist_ok=True)

        parts = []
        if prefix:
            # Strip file extension from prefix (e.g. "{{number}}.png" → "{{number}}")
            prefix = os.path.splitext(prefix)[0]
            parts.append(prefix)
        parts.append(f"{stt:03d}")
        if img_idx > 0:
            parts.append(f"{img_idx + 1}")
        filename = "_".join(parts) + ".png"
        filepath = os.path.join(output_folder, filename)

        image_data = base64.b64decode(encoded_image)
        with open(filepath, "wb") as f:
            f.write(image_data)

        return filepath


# ── Main Page ────────────────────────────────────────────────────────


class ImageCreatorPage(QWidget):
    """Main image creator page with config panel, queue table, and toolbar."""

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

    # ── Workflow Persistence ─────────────────────────────────────────

    def _save_workflow(self, flow_id: int, workflow_id: str, workflow_name: str):
        """Persist workflow data to QSettings keyed by flow_id."""
        s = QSettings("Whisk", "Workflows")
        s.setValue(f"flow_{flow_id}/workflow_id", workflow_id)
        s.setValue(f"flow_{flow_id}/workflow_name", workflow_name)
        s.sync()
        logger.info(f"💾 Workflow saved: flow={flow_id} → {workflow_id}")

    def _load_workflow(self, flow_id: int):
        """Restore workflow data from QSettings for the given flow_id."""
        s = QSettings("Whisk", "Workflows")
        wf_id = s.value(f"flow_{flow_id}/workflow_id", "")
        wf_name = s.value(f"flow_{flow_id}/workflow_name", "")

        if wf_id:
            self._workflow_id = wf_id
            self._workflow_name = wf_name
            logger.info(f"📂 Workflow restored: flow={flow_id} → {wf_id}")
            # Update config panel to show linked status
            if hasattr(self, "_config"):
                self._config.set_workflow_status(
                    f"✅ Workflow linked\n{wf_id[:16]}..."
                )
        else:
            self._workflow_id = ""
            self._workflow_name = ""

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

    def _on_prompt_edited(self, task_id: str, new_prompt: str):
        """Persist prompt edits from the table to the API store."""
        normalized = PromptNormalizer.normalize(new_prompt)
        self.api.update_task(task_id, {"prompt": normalized})
        logger.info(f"✏️ Prompt updated for task {task_id[:8]}...")

    def _on_selection_changed(self, ids: list[str]):
        """Track selected task IDs."""
        self._selected_ids = ids

    def _on_add_to_queue(self, config: dict):
        """Add task(s) from config panel to the queue."""
        prompt_text = config.get("prompt", "").strip()
        if not prompt_text:
            return

        # Check if entire block is JSON (single JSON prompt)
        if PromptNormalizer.is_json_prompt(prompt_text):
            lines = [PromptNormalizer.normalize_json(prompt_text)]
        else:
            # Split by newlines → one task per line, normalize each
            lines = [
                PromptNormalizer.normalize(line.strip())
                for line in prompt_text.split("\n")
                if line.strip()
            ]

        MAX_PROMPTS = 300
        if len(lines) > MAX_PROMPTS:
            StyledMessageBox.warning(
                self, "Error",
                f"Tối đa {MAX_PROMPTS} prompt mỗi lần.\n"
                f"Bạn đang thêm {len(lines)} prompt."
            )
            return

        for line in lines:
            task_data = {
                "model": config.get("model", "IMAGEN_3_5"),
                "aspect_ratio": config.get("aspect_ratio", "16:9"),
                "quality": config.get("quality", "1K"),
                "prompt": line,
                "images_per_prompt": config.get("images_per_prompt", 1),
                "reference_images": [],
                "output_folder": config.get("output_folder", ""),
                "filename_prefix": config.get("filename_prefix", ""),
            }
            self.api.add_to_queue(task_data)

        self.refresh_data()

    def _on_add_row(self):
        """Add an empty row to the queue."""
        self.api.add_to_queue({
            "prompt": "",
            "model": "IMAGEN_3_5",
            "aspect_ratio": "16:9",
            "quality": "1K",
        })
        self.refresh_data()

    def _on_delete_selected(self):
        """Remove selected rows from the queue."""
        if self._selected_ids:
            self.api.delete_tasks(self._selected_ids)
            self._selected_ids.clear()
            self.refresh_data()

    def _on_delete_all(self):
        """Clear the entire queue after confirmation."""
        if StyledMessageBox.question(
            self,
            self.translator.t("queue.confirm_delete_all"),
            self.translator.t("queue.confirm_delete_all_msg"),
        ):
            self.api.clear_queue()
            self.refresh_data()

    def _on_retry_errors(self):
        """Reset error tasks to pending."""
        self._retry_counts.clear()  # Manual retry resets all counts
        self._auto_retry_timer.stop()
        self.api.retry_errors()
        self.refresh_data()

    def _on_clear_checkpoint(self):
        """Clear checkpoint file and queue after confirmation."""
        if StyledMessageBox.question(
            self, "Clear Checkpoint",
            "Xóa tất cả dữ liệu đã lưu (checkpoint)?\nHành động này không thể hoàn tác.",
            confirm_text="Xóa", cancel_text="Hủy",
        ):
            self.api.clear_checkpoint()
            self.refresh_data()

    def _on_ref_images_picked(self, paths: list):
        """Handle reference images picked from file dialog."""
        pass

    # ── Workflow ──────────────────────────────────────────────────────

    def _on_workflow_requested(self):
        """Handle '🆕 New Workflow' button click. Creates & links the workflow."""
        if not self.workflow_api:
            self._config.set_workflow_status("⚠️ Workflow API not available")
            return
        if not self.cookie_api or not self._active_flow_id:
            self._config.set_workflow_status("⚠️ No active project or cookie API")
            return

        self._config.set_workflow_status("⏳ Creating workflow on Labs...")

        # Get active cookie for session token
        keys_resp = self.cookie_api.get_api_keys(
            flow_id=self._active_flow_id,
            provider="WHISK",
            status="active",
        )

        if not keys_resp.success or not keys_resp.data:
            self._config.set_workflow_status("❌ No cookies available.\nAdd a WHISK cookie first.", error=True)
            return

        items = keys_resp.data.get("items", [])
        if not items:
            self._config.set_workflow_status("❌ No active cookies found.\nAdd a WHISK cookie first.", error=True)
            return

        # Filter out expired cookies
        from datetime import datetime
        now = datetime.utcnow()
        live_items = []
        for item in items:
            expired_str = item.get("expired", "")
            if expired_str:
                try:
                    expired_dt = datetime.fromisoformat(expired_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if expired_dt < now:
                        continue  # Skip expired cookie
                except (ValueError, TypeError):
                    pass
            live_items.append(item)

        if not live_items:
            # Show last expired time for context
            last_expired = items[0].get("expired", "N/A")
            label = items[0].get("label", "")
            self._config.set_workflow_status(
                f"❌ All cookies expired!\n{label}\nExpired: {last_expired}\nAdd a new cookie.",
                error=True,
            )
            return

        items = live_items

        cookie = items[0]
        metadata = cookie.get("metadata", {})
        cookies = metadata.get("cookies", {})
        session_token = cookies.get("__Secure-next-auth.session-token", "")
        csrf_token = cookies.get("__Host-next-auth.csrf-token", "")

        if not session_token:
            self._config.set_workflow_status("❌ Cookie has no session token.")
            return

        # Step 1: Create workflow on Labs
        wf_resp = self.workflow_api.create_workflow(session_token, csrf_token)
        if not wf_resp.success:
            self._config.set_workflow_status(f"❌ Create failed:\n{wf_resp.message}")
            return

        workflow_id = wf_resp.data.get("workflowId", "")
        workflow_name = wf_resp.data.get("workflowName", "")
        logger.info(f"🆕 Workflow created: {workflow_id} ({workflow_name})")

        # Step 2: Link to server flow
        link_resp = self.workflow_api.link_workflow(
            flow_id=self._active_flow_id,
            project_id=workflow_id,
            project_name=workflow_name,
        )

        if link_resp.success:
            self._config.set_workflow_status(
                f"✅ Workflow created & linked!\n{workflow_id[:16]}..."
            )
            self._workflow_id = workflow_id
            self._workflow_name = workflow_name
            self._save_workflow(self._active_flow_id, workflow_id, workflow_name)
            logger.info(f"🔗 Workflow linked: {workflow_id} → flow {self._active_flow_id}")

            # Auto-add to queue if prompts exist
            prompt_text = self._config._prompt_input.toPlainText().strip()
            if prompt_text:
                logger.info("➕ Auto-adding prompts to queue after workflow link")
                self._config._on_add()
        else:
            self._config.set_workflow_status(
                f"⚠️ Created but link failed:\n{link_resp.message}"
            )

    # ── Run tasks (background) ────────────────────────────────────────

    def _on_run_all(self):
        """Run all pending tasks in background."""
        self._retry_counts.clear()  # Manual run resets all counts
        self._auto_retry_timer.stop()
        self._run_tasks()

    def _on_run_selected(self):
        """Run selected pending tasks in background."""
        if not self._selected_ids:
            StyledMessageBox.information(self, "Info", "No tasks selected.")
            return
        self._run_tasks(task_ids=self._selected_ids)

    def _run_tasks(self, task_ids: list[str] | None = None):
        """Start background worker for pending tasks."""
        if self._is_generating:
            logger.warning("Generation already in progress, ignoring run request")
            return

        if not self.workflow_api:
            StyledMessageBox.warning(self, "Error", "Workflow API not available.")
            return
        if not self.cookie_api or not self._active_flow_id:
            StyledMessageBox.warning(self, "Error", "No active project. Select a project first.")
            return

        # Step 1: Get Google access_token from active cookie
        google_token, workflow_id, error = self._get_google_access_token()
        if error:
            StyledMessageBox.warning(self, "Error", error)
            return

        if not workflow_id:
            workflow_id = self._workflow_id
        if not workflow_id:
            StyledMessageBox.warning(
                self, "Error",
                "No workflow linked to this project.\n"
                "Click '🆕 New Workflow' first to create and link a workflow."
            )
            return

        # Step 2: Get pending tasks from queue
        resp = self.api.get_queue()
        if not resp.success:
            return

        tasks = resp.data or []

        # When running selected tasks, reset completed/error → pending
        if task_ids is not None:
            for t in tasks:
                if t.get("id") in task_ids and t.get("status") in ("completed", "error"):
                    self.api.update_task(t["id"], {
                        "status": "pending",
                        "output_images": [],
                        "error_message": "",
                    })
                    t["status"] = "pending"

        pending = [
            t for t in tasks
            if t.get("status") == "pending"
            and (task_ids is None or t.get("id") in task_ids)
        ]

        if not pending:
            StyledMessageBox.information(self, "Info", "No pending tasks to run.")
            return

        self._is_generating = True
        self.refresh_data()  # Update UI to show reset status
        logger.info(f"▶️ Starting generation for {len(pending)} tasks")

        # Get concurrency from config (default 2)
        concurrency = self._config._concurrency_spin.value()

        # Start background worker
        self._worker = GenerationWorker(
            workflow_api=self.workflow_api,
            google_token=google_token,
            workflow_id=workflow_id,
            tasks=pending,
            concurrency=concurrency,
            workflow_name=self._workflow_name,
            flow_name=self._flow_name,
            parent=self,
        )
        self._worker.task_progress.connect(self._on_task_progress)
        self._worker.finished_all.connect(self._on_worker_finished)
        self._worker.start()

    def _on_task_progress(self, task_id: str, progress: int, status: str, extra: dict):
        """Handle progress updates from the background worker."""
        update_data = {"status": status, "progress": progress}
        update_data.update(extra)

        # Record completion timestamp for finished tasks
        if status in ("completed", "error"):
            from datetime import datetime
            update_data["completed_at"] = datetime.now().isoformat(timespec="seconds")

        self.api.update_task(task_id, update_data)

        if status == "running":
            self._running_task_ids.add(task_id)
            # Track start time on first running update
            if task_id not in self._task_start_times:
                self._task_start_times[task_id] = time.time()
            self._local_progress[task_id] = max(
                self._local_progress.get(task_id, 0), progress
            )
            if not self._progress_timer.isActive():
                self._progress_timer.start()
            # Lightweight update — no full table rebuild
            elapsed = int(time.time() - self._task_start_times[task_id])
            self._table.update_task_progress(
                task_id, self._local_progress[task_id], status,
                elapsed_seconds=elapsed,
            )
        else:
            # Task completed or errored — clean up local tracking
            self._running_task_ids.discard(task_id)
            self._local_progress.pop(task_id, None)
            self._task_start_times.pop(task_id, None)
            # Track retry count for errored tasks
            if status == "error":
                self._retry_counts[task_id] = self._retry_counts.get(task_id, 0) + 1
            # Full refresh needed to show action buttons / output images
            self.refresh_data()

    def _tick_progress(self):
        """Smoothly animate progress bars — pure local, no API calls."""
        if not self._running_task_ids:
            self._progress_timer.stop()
            return

        for tid in list(self._running_task_ids):
            current = self._local_progress.get(tid, 0)
            if current < 99:
                increment = random.randint(2, 5)
                new_pct = min(current + increment, 99)
                self._local_progress[tid] = new_pct
            elapsed = int(time.time() - self._task_start_times.get(tid, time.time()))
            self._table.update_task_progress(
                tid, self._local_progress.get(tid, 0), "running",
                elapsed_seconds=elapsed,
            )

    def _on_worker_finished(self):
        """Called when all tasks complete."""
        self._is_generating = False
        self._worker = None
        self._running_task_ids.clear()
        self._local_progress.clear()
        self._task_start_times.clear()
        self._progress_timer.stop()
        logger.info("✅ Generation batch complete")
        self.refresh_data()

        # Show completion toast
        self._show_completion_toast()

        # Auto-retry: schedule retry for tasks that haven't exceeded MAX_RETRIES
        if self._config.is_auto_retry_enabled:
            self._schedule_auto_retry()

    def _show_completion_toast(self):
        """Show a toast summarizing batch results."""
        response = self.api.get_queue()
        tasks = response.data or []
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        errors = sum(1 for t in tasks if t.get("status") == "error")

        if errors > 0:
            msg = f"Hoàn thành {completed} ảnh, {errors} lỗi"
            self._toast.show_message(msg, icon="⚠️",
                                     bg_start="#F59E0B", bg_end="#D97706")
        else:
            msg = f"Hoàn thành {completed} ảnh thành công!"
            self._toast.show_message(msg, icon="✅")

    def _schedule_auto_retry(self):
        """Check for retryable errors and schedule auto-retry after 60s."""
        response = self.api.get_queue()
        if not response.data:
            return

        retryable = [
            t for t in response.data
            if t.get("status") == "error"
            and self._retry_counts.get(t["id"], 0) <= self.MAX_RETRIES
        ]

        if not retryable:
            logger.info("🔁 No retryable errors (all exceeded max retries)")
            return

        logger.info(
            f"🔁 Auto-retry: {len(retryable)} task(s) will retry in 60s "
            f"(attempt {self._retry_counts.get(retryable[0]['id'], 0)}/{self.MAX_RETRIES + 1})"
        )
        self._auto_retry_timer.start()

    def _do_auto_retry(self):
        """Execute the scheduled auto-retry."""
        if self._is_generating:
            logger.info("🔁 Auto-retry skipped: generation already running")
            return

        if not self._config.is_auto_retry_enabled:
            logger.info("🔁 Auto-retry cancelled: toggle disabled by user")
            return

        response = self.api.get_queue()
        if not response.data:
            return

        retryable_ids = [
            t["id"] for t in response.data
            if t.get("status") == "error"
            and self._retry_counts.get(t["id"], 0) <= self.MAX_RETRIES
        ]

        if not retryable_ids:
            return

        logger.info(f"🔁 Auto-retrying {len(retryable_ids)} task(s)...")

        # Reset only retryable error tasks to pending
        for t in response.data:
            if t["id"] in retryable_ids:
                self.api.update_task(t["id"], {
                    "status": "pending",
                    "progress": 0,
                    "elapsed_seconds": 0,
                    "error_message": "",
                })

        self.refresh_data()
        self._run_tasks(task_ids=retryable_ids)

    # ── Auth helpers ──────────────────────────────────────────────────

    def _get_google_access_token(self) -> tuple[str, str, str | None]:
        """
        Get Google OAuth access_token and workflowId from the active cookie.

        Returns:
            (access_token, workflow_id, error_message_or_None)
        """
        try:
            resp = self.cookie_api.get_api_keys(
                flow_id=self._active_flow_id,
                provider="WHISK",
                status="active",
            )
            if not resp.success or not resp.data:
                return "", "", "No cookies found. Add a cookie first."

            items = resp.data.get("items", [])
            if not items:
                return "", "", "No active cookies found."

            # Use first active cookie — access_token is in the "value" field
            cookie = items[0]
            access_token = cookie.get("value", "")

            if not access_token:
                return "", "", "Cookie has no Google access_token. Try refreshing the cookie."

            # workflowId is not stored in cookie data
            workflow_id = ""

            return access_token, workflow_id, None

        except Exception as e:
            logger.error(f"Failed to get Google access_token: {e}")
            return "", "", f"Error getting access token: {e}"

    # ── Download / Save ───────────────────────────────────────────────

    def _on_download(self, task_id: str):
        """Handle 💾 save button — copy generated images to user-chosen folder."""
        task_resp = self.api.get_task(task_id)
        if not task_resp.success:
            return

        task_data = task_resp.data
        output_images = task_data.get("output_images", [])
        if not output_images:
            StyledMessageBox.information(self, "Info", "No generated images to save.")
            return

        # Open folder picker
        folder = QFileDialog.getExistingDirectory(
            self, self.translator.t("config.output_folder"),
            os.path.expanduser("~/Downloads"),
        )
        if not folder:
            return

        # Copy images using prefix + stt naming
        prefix = task_data.get("filename_prefix", "")
        stt = task_data.get("stt", 0)
        saved = 0
        for idx, src_path in enumerate(output_images):
            if not os.path.isfile(src_path):
                continue
            parts = []
            if prefix:
                parts.append(prefix)
            parts.append(f"{stt:03d}")
            if idx > 0:
                parts.append(f"{idx + 1}")
            ext = os.path.splitext(src_path)[1] or ".png"
            filename = "_".join(parts) + ext
            dst_path = os.path.join(folder, filename)
            shutil.copy2(src_path, dst_path)
            saved += 1
            logger.info(f"💾 Saved: {dst_path}")

        logger.info(f"✅ Saved {saved} image(s) to: {folder}")

    # ── Download All ─────────────────────────────────────────────────

    def _on_download_all(self):
        """Handle 📥 button — copy all completed output images to user-chosen folder."""
        # Gather all completed tasks with output images
        queue_resp = self.api.get_queue()
        if not queue_resp.success:
            return

        all_tasks = queue_resp.data or []
        completed = [
            t for t in all_tasks
            if t.get("status") == "completed" and t.get("output_images")
        ]

        if not completed:
            StyledMessageBox.information(
                self, "Info",
                self.translator.t("download.no_images"),
            )
            return

        # Ask user for destination folder
        folder = QFileDialog.getExistingDirectory(
            self, self.translator.t("toolbar.download_all"),
            os.path.expanduser("~/Downloads"),
        )
        if not folder:
            return

        saved = 0
        for task_data in completed:
            prefix = task_data.get("filename_prefix", "")
            stt = task_data.get("stt", 0)
            for idx, src_path in enumerate(task_data.get("output_images", [])):
                if not os.path.isfile(src_path):
                    continue
                parts = []
                if prefix:
                    parts.append(prefix)
                parts.append(f"{stt:03d}")
                if idx > 0:
                    parts.append(f"{idx + 1}")
                ext = os.path.splitext(src_path)[1] or ".png"
                filename = "_".join(parts) + ext
                dst_path = os.path.join(folder, filename)
                shutil.copy2(src_path, dst_path)
                saved += 1
                logger.info(f"📥 Downloaded: {dst_path}")

        logger.info(f"✅ Downloaded {saved} image(s) to: {folder}")

    # ── Open Folder ──────────────────────────────────────────────────

    def _on_open_folder(self, task_id: str):
        """Handle 📂 button — open output folder in system file manager."""
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        task_resp = self.api.get_task(task_id)
        if not task_resp.success:
            return

        task_data = task_resp.data

        # Try output_folder first, then derive from output_images
        folder = task_data.get("output_folder", "")
        if not folder or not os.path.isdir(folder):
            output_images = task_data.get("output_images", [])
            if output_images:
                folder = os.path.dirname(output_images[0])

        if not folder or not os.path.isdir(folder):
            # Fallback to default download folder with project name
            base = os.path.join(os.path.expanduser("~"), "Downloads", "whisk_pro")
            if self._workflow_name:
                safe_wf = self._workflow_name.replace("/", "_").replace(":", "_").strip()
                if self._flow_name:
                    safe_flow = self._flow_name.replace("/", "_").replace(":", "_").strip()
                    folder_name = f"{safe_flow}_{safe_wf}"
                else:
                    folder_name = safe_wf
                folder = os.path.join(base, folder_name)
            elif self._flow_name:
                safe_flow = self._flow_name.replace("/", "_").replace(":", "_").strip()
                folder = os.path.join(base, safe_flow)
            else:
                folder = base

        if os.path.isdir(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        else:
            StyledMessageBox.information(
                self, "Info",
                self.translator.t("queue.folder_not_found"),
            )

    def retranslate(self):
        """Refresh data after language change to update status labels."""
        self.refresh_data()
