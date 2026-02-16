"""
Whisk Desktop — Image Creator Page.

Main page that assembles ConfigPanel + TaskQueueTable + QueueToolbar.
Background image generation with real-time progress tracking.
"""
import base64
import logging
import os
import shutil
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QFileDialog,
)
from PySide6.QtCore import Qt, QThread, Signal as QSignal, QTimer
from app.widgets.config_panel import ConfigPanel
from app.widgets.task_queue_table import TaskQueueTable
from app.widgets.queue_toolbar import QueueToolbar
from app.widgets.log_panel import LogPanel
from app.widgets.styled_message_box import StyledMessageBox

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
        parent=None,
    ):
        super().__init__(parent)
        self.workflow_api = workflow_api
        self.google_token = google_token
        self.workflow_id = workflow_id
        self.tasks = tasks
        self.concurrency = max(1, concurrency)
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        logger.info(f"Worker starting with concurrency={self.concurrency} for {len(self.tasks)} tasks")
        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = {
                pool.submit(self._process_task, task): task
                for task in self.tasks
            }
            for future in as_completed(futures):
                if self._stop_flag:
                    break
                # Exceptions are already handled inside _process_task
                try:
                    future.result()
                except Exception:
                    pass
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

                gen_resp = self.workflow_api.generate_image(
                    google_access_token=self.google_token,
                    workflow_id=self.workflow_id,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )

                if not gen_resp.success:
                    raise Exception(gen_resp.message)

                # Save image to file
                encoded_image = gen_resp.data.get("encoded_image", "")
                if encoded_image:
                    save_folder = output_folder or os.path.join(
                        os.path.expanduser("~"), "Downloads", "whisk_pro"
                    )
                    saved_path = self._save_image(
                        encoded_image, save_folder,
                        filename_prefix, task.get("stt", 0), img_idx,
                    )
                    saved_paths.append(saved_path)
                    logger.info(f"Image saved: {saved_path}")

            elapsed = int(time.time() - start_time)
            self.task_progress.emit(task_id, 100, "completed", {
                "elapsed_seconds": elapsed,
                "output_images": saved_paths,
            })

        except Exception as e:
            elapsed = int(time.time() - start_time)
            logger.error(f"Task {task_id} failed: {e}")
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

    def __init__(self, translator, api, parent=None,
                 workflow_api=None, cookie_api=None, active_flow_id=None):
        super().__init__(parent)
        self.translator = translator
        self.api = api
        self.workflow_api = workflow_api
        self.cookie_api = cookie_api
        self._active_flow_id = active_flow_id
        self._workflow_id: str = ""  # Set during workflow creation or loaded from server
        self.translator.language_changed.connect(self.retranslate)
        self._selected_ids: list[str] = []
        self._is_generating = False
        self._worker: GenerationWorker | None = None
        self._running_task_ids: set[str] = set()  # Track running tasks for progress timer
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(500)  # tick every 500ms
        self._progress_timer.timeout.connect(self._tick_progress)
        self._setup_ui()
        self._connect_signals()
        self.refresh_data()

    def set_active_flow_id(self, flow_id):
        """Update the active flow ID (called when project changes)."""
        self._active_flow_id = int(flow_id) if flow_id else None

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

        # Table download + open folder
        self._table.download_clicked.connect(self._on_download)
        self._table.open_folder_clicked.connect(self._on_open_folder)

    def refresh_data(self):
        """Reload the queue from API."""
        response = self.api.get_queue()
        if response.success:
            self._table.load_data(response.data or [])

    def _on_selection_changed(self, ids: list[str]):
        """Track selected task IDs."""
        self._selected_ids = ids

    def _on_add_to_queue(self, config: dict):
        """Add task(s) from config panel to the queue."""
        prompt = config.get("prompt", "").strip()
        if not prompt:
            return

        # Split by newlines → one task per line
        lines = [line.strip() for line in prompt.split("\n") if line.strip()]
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
            self._config.set_workflow_status("❌ No cookies available.\nAdd a WHISK cookie first.")
            return

        items = keys_resp.data.get("items", [])
        if not items:
            self._config.set_workflow_status("❌ No active cookies found.\nAdd a WHISK cookie first.")
            return

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
        logger.info(f"Workflow created: {workflow_id} ({workflow_name})")

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
            logger.info(f"Workflow linked: {workflow_id} → flow {self._active_flow_id}")

            # Auto-add to queue if prompts exist
            prompt_text = self._config._prompt_input.toPlainText().strip()
            if prompt_text:
                logger.info("Auto-adding prompts to queue after workflow link")
                self._config._on_add()
        else:
            self._config.set_workflow_status(
                f"⚠️ Created but link failed:\n{link_resp.message}"
            )

    # ── Run tasks (background) ────────────────────────────────────────

    def _on_run_all(self):
        """Run all pending tasks in background."""
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
        pending = [
            t for t in tasks
            if t.get("status") == "pending"
            and (task_ids is None or t.get("id") in task_ids)
        ]

        if not pending:
            StyledMessageBox.information(self, "Info", "No pending tasks to run.")
            return

        self._is_generating = True
        logger.info(f"Starting generation for {len(pending)} tasks")

        # Get concurrency from config (default 2)
        concurrency = self._config._concurrency_spin.value()

        # Start background worker
        self._worker = GenerationWorker(
            workflow_api=self.workflow_api,
            google_token=google_token,
            workflow_id=workflow_id,
            tasks=pending,
            concurrency=concurrency,
            parent=self,
        )
        self._worker.task_progress.connect(self._on_task_progress)
        self._worker.finished_all.connect(self._on_worker_finished)
        self._worker.start()

    def _on_task_progress(self, task_id: str, progress: int, status: str, extra: dict):
        """Handle progress updates from the background worker."""
        update_data = {"status": status, "progress": progress}
        update_data.update(extra)
        self.api.update_task(task_id, update_data)

        if status == "running":
            self._running_task_ids.add(task_id)
            if not self._progress_timer.isActive():
                self._progress_timer.start()
        else:
            # Task completed or errored — remove from running set
            self._running_task_ids.discard(task_id)

        self.refresh_data()

    def _tick_progress(self):
        """Smoothly increment progress of all running tasks toward 99%."""
        if not self._running_task_ids:
            self._progress_timer.stop()
            return

        resp = self.api.get_queue()
        if not resp.success:
            return

        updated = False
        for task_data in (resp.data or []):
            tid = task_data.get("id", "")
            if tid not in self._running_task_ids:
                continue
            current = task_data.get("progress", 0)
            if current < 99:
                # Increment by 2-5%, cap at 99
                increment = random.randint(2, 5)
                new_pct = min(current + increment, 99)
                self.api.update_task(tid, {"progress": new_pct})
                updated = True

        if updated:
            self.refresh_data()

    def _on_worker_finished(self):
        """Called when all tasks complete."""
        self._is_generating = False
        self._worker = None
        self._running_task_ids.clear()
        self._progress_timer.stop()
        logger.info("Generation batch complete")
        self.refresh_data()

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
            logger.info(f"Saved: {dst_path}")

        StyledMessageBox.information(
            self, "✅ Saved",
            f"Saved {saved} image(s) to:\n{folder}",
        )

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
            # Fallback to default download folder
            folder = os.path.join(os.path.expanduser("~"), "Downloads", "whisk_pro")

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
