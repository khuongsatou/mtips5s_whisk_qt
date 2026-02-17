"""
Whisk Desktop — Image Creator Page Handlers.

Mixin class providing queue operations, workflow management,
generation execution, auto-retry, download, and auth helpers
for ImageCreatorPage.
"""
import logging
import os
import random
import shutil
import time

from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QSettings

from app.prompt_normalizer import PromptNormalizer
from app.widgets.styled_message_box import StyledMessageBox

logger = logging.getLogger("whisk.image_creator")


class PageHandlersMixin:
    """Mixin providing event handlers for ImageCreatorPage."""

    # ── Queue Operations ──────────────────────────────────────────────

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
                "reference_images_by_cat": {
                    "title": config.get("ref_title_images", []),
                    "scene": config.get("ref_scene_images", []),
                    "style": config.get("ref_style_images", []),
                },
                "preloaded_media_inputs": config.get("preloaded_media_inputs", []),
                "output_folder": config.get("output_folder", ""),
                "filename_prefix": config.get("filename_prefix", ""),
            }
            self.api.add_to_queue(task_data)

        self.refresh_data()

    def _on_request_upload_ref(self, category: str, ref_by_cat: dict):
        """Pre-upload reference images for single mode (background thread)."""
        google_token, workflow_id, session_token, error = self._get_google_access_token()
        if error:
            self._config.set_preloaded_media_inputs(category, [])
            return

        from app.api.workflow_api import WorkflowApiClient
        from app.pages.image_creator_page.workers import _RefUploadWorker

        worker = _RefUploadWorker(
            workflow_api=WorkflowApiClient(),
            session_token=session_token,
            workflow_id=workflow_id,
            ref_by_cat=ref_by_cat,
            parent=self,
        )
        worker._category = category  # store category for callback
        worker.finished_upload.connect(self._on_ref_upload_done)
        # Store per-category worker to prevent GC
        if not hasattr(self, '_ref_upload_workers'):
            self._ref_upload_workers = {}
        self._ref_upload_workers[category] = worker
        worker.start()

    def _on_ref_upload_done(self, media_inputs: list):
        """Receive results from background ref upload worker."""
        worker = self.sender()
        category = getattr(worker, '_category', '')
        self._config.set_preloaded_media_inputs(category, media_inputs)
        if hasattr(self, '_ref_upload_workers'):
            self._ref_upload_workers.pop(category, None)
        if worker:
            worker.deleteLater()

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
        from app.pages.image_creator_page.workers import GenerationWorker

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
        google_token, workflow_id, session_token, error = self._get_google_access_token()
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

        # In single mode, inject current preloaded media IDs into all tasks
        # so the worker skips re-uploading reference images
        if self._config._current_ref_mode == "single":
            preloaded = self._config._get_all_preloaded()
            if preloaded:
                for t in pending:
                    t["preloaded_media_inputs"] = preloaded
                logger.info(f"🔗 Single mode: injected {len(preloaded)} preloaded ref(s) into {len(pending)} task(s)")

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
            session_token=session_token,
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
            # Track upload_status for ref image uploads
            upload_status = extra.get("upload_status", "")
            if upload_status:
                self._upload_status[task_id] = upload_status
            elif upload_status == "":
                self._upload_status.pop(task_id, None)
            if not self._progress_timer.isActive():
                self._progress_timer.start()
            # Lightweight update — no full table rebuild
            elapsed = int(time.time() - self._task_start_times[task_id])
            self._table.update_task_progress(
                task_id, self._local_progress[task_id], status,
                elapsed_seconds=elapsed,
                upload_status=self._upload_status.get(task_id, ""),
            )
        else:
            # Task completed or errored — clean up local tracking
            self._running_task_ids.discard(task_id)
            self._local_progress.pop(task_id, None)
            self._task_start_times.pop(task_id, None)
            self._upload_status.pop(task_id, None)
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
                upload_status=self._upload_status.get(tid, ""),
            )

    def _on_worker_finished(self):
        """Called when all tasks complete."""
        self._is_generating = False
        self._worker = None
        self._running_task_ids.clear()
        self._local_progress.clear()
        self._task_start_times.clear()
        self._upload_status.clear()
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

    def _get_google_access_token(self) -> tuple[str, str, str, str | None]:
        """
        Get Google OAuth access_token, session_token, and workflowId from the active cookie.

        Returns:
            (access_token, workflow_id, session_token, error_message_or_None)
        """
        try:
            resp = self.cookie_api.get_api_keys(
                flow_id=self._active_flow_id,
                provider="WHISK",
                status="active",
            )
            if not resp.success or not resp.data:
                return "", "", "", "No cookies found. Add a cookie first."

            items = resp.data.get("items", [])
            if not items:
                return "", "", "", "No active cookies found."

            # Use first active cookie — access_token is in the "value" field
            cookie = items[0]
            access_token = cookie.get("value", "")

            if not access_token:
                return "", "", "", "Cookie has no Google access_token. Try refreshing the cookie."

            # Extract session_token from cookie metadata
            metadata = cookie.get("metadata", {})
            cookies_dict = metadata.get("cookies", {})
            session_token = cookies_dict.get("__Secure-next-auth.session-token", "")

            # workflowId is not stored in cookie data
            workflow_id = ""

            return access_token, workflow_id, session_token, None

        except Exception as e:
            logger.error(f"Failed to get Google access_token: {e}")
            return "", "", "", f"Error getting access token: {e}"

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

    # ── Retranslation ────────────────────────────────────────────────

    def retranslate(self):
        """Refresh data after language change to update status labels."""
        self.refresh_data()
