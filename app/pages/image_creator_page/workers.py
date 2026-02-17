"""
Whisk Desktop — Background Workers for Image Generation.

GenerationWorker: Runs image generation tasks with concurrency.
_RefUploadWorker: Pre-uploads reference images in background.
"""
import base64
import logging
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QThread, Signal as QSignal

logger = logging.getLogger("whisk.image_creator")


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
        session_token: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.workflow_api = workflow_api
        self.google_token = google_token
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.flow_name = flow_name
        self.session_token = session_token
        self.tasks = tasks
        self.concurrency = max(1, concurrency)
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    TASK_TIMEOUT = 60  # 60 seconds per task

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
            # Check for preloaded media_inputs (single mode)
            preloaded = task.get("preloaded_media_inputs", [])
            if preloaded:
                media_inputs = list(preloaded)
                self.task_progress.emit(
                    task_id, 10, "running",
                    {"upload_status": f"✅ Using {len(media_inputs)} preloaded ref(s)"},
                )
            else:
                # Upload reference images (once per task, before generation loop)
                media_inputs = []
                ref_by_cat = task.get("reference_images_by_cat", {})

                # Count total ref images for progress
                all_refs = []
                for cat in ("title", "scene", "style"):
                    for img_path in ref_by_cat.get(cat, []):
                        all_refs.append((cat, img_path))

                for ref_idx, (cat, img_path) in enumerate(all_refs):
                    if self._stop_flag:
                        break
                    # Progress: 5–10% range for uploads
                    upload_pct = 5 + int((ref_idx / max(len(all_refs), 1)) * 5)
                    self.task_progress.emit(
                        task_id, upload_pct, "running",
                        {"upload_status": f"📸 Uploading {ref_idx + 1}/{len(all_refs)} ({cat})…"},
                    )
                    try:
                        resp = self.workflow_api.upload_reference_image(
                            session_token=self.session_token,
                            image_path=img_path,
                            category=cat,
                            workflow_id=self.workflow_id,
                        )
                        if resp.success:
                            media_inputs.append(resp.data)
                    except Exception as e:
                        logger.warning(f"⚠️ Ref image upload failed ({cat}): {e}")

                # Clear upload status after uploads complete
                if all_refs:
                    self.task_progress.emit(
                        task_id, 10, "running",
                        {"upload_status": ""},
                    )

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

                # Pass remaining time as HTTP timeout so it doesn't exceed TASK_TIMEOUT
                remaining = max(5, int(self.TASK_TIMEOUT - elapsed))

                gen_resp = self.workflow_api.generate_image(
                    google_access_token=self.google_token,
                    workflow_id=self.workflow_id,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    media_inputs=media_inputs or None,
                    timeout=remaining,
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


# ── Background worker for ref image pre-upload ──────────────────────


class _RefUploadWorker(QThread):
    """Uploads reference images in background for single mode."""

    finished_upload = QSignal(list)  # emits list of media_input dicts

    def __init__(self, workflow_api, session_token, workflow_id, ref_by_cat, parent=None):
        super().__init__(parent)
        self.workflow_api = workflow_api
        self.session_token = session_token
        self.workflow_id = workflow_id
        self.ref_by_cat = ref_by_cat

    def run(self):
        media_inputs = []
        for cat, paths in self.ref_by_cat.items():
            for img_path in paths:
                try:
                    resp = self.workflow_api.upload_reference_image(
                        session_token=self.session_token,
                        image_path=img_path,
                        category=cat,
                        workflow_id=self.workflow_id,
                    )
                    if resp.success:
                        media_inputs.append(resp.data)
                except Exception as e:
                    logger.warning(f"⚠️ Pre-upload failed ({cat}): {e}")
        self.finished_upload.emit(media_inputs)
