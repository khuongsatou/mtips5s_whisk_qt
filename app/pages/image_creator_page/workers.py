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
        captcha_bridge=None,
        poll_interval: int = 30,
        api_timeout: int = 60,
        parent=None,
    ):
        super().__init__(parent)
        self.workflow_api = workflow_api
        self.google_token = google_token
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.flow_name = flow_name
        self.session_token = session_token
        self.captcha_bridge = captcha_bridge
        self.poll_interval = max(5, poll_interval)
        self.api_timeout = max(30, min(180, api_timeout))
        self.tasks = tasks
        self.concurrency = max(1, concurrency)
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    TASK_TIMEOUT = 600  # 10 min total (generation + polling)
    CAPTCHA_TIMEOUT = 30  # Wait up to 30s for captcha token
    POLL_MAX_TIME = 480  # Max 8 min polling after generation starts

    def _fetch_captcha_token(self, task_id: str) -> str:
        """Request and wait for a unique captcha token from the bridge.

        Uses bridge._token_queue (thread-safe queue.Queue) so each
        concurrent worker gets exactly one unique token.
        """
        if not self.captcha_bridge:
            raise RuntimeError(
                "Captcha bridge chưa chạy! Bật Extension mode (🔐 → 🔌 Extension) để lấy captcha token."
            )

        bridge = self.captcha_bridge

        # Request a new token from extension
        bridge.request_token(action="VIDEO_GENERATION", count=1)
        self.task_progress.emit(task_id, 15, "running", {"upload_status": "🔐 Waiting for captcha token..."})
        logger.info("🔐 Requesting captcha token from extension...")

        # Block until a unique token is available from the queue
        try:
            token = bridge._token_queue.get(timeout=self.CAPTCHA_TIMEOUT)
            if token:
                logger.info(f"🔐 Got captcha token ({len(token)} chars)")
                self.task_progress.emit(task_id, 18, "running", {"upload_status": "🔐 Captcha token received!"})
                return token
        except Exception:
            pass

        raise RuntimeError(
            "Không nhận được captcha token sau 30s. "
            "Kiểm tra Extension đã cài và mở tab labs.google/fx."
        )


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
        aspect_ratio = task.get("aspect_ratio", "VIDEO_ASPECT_RATIO_LANDSCAPE")
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

                # Fetch captcha token before API call
                recaptcha_token = self._fetch_captcha_token(task_id)

                self.task_progress.emit(
                    task_id, 20, "running",
                    {"upload_status": "🎬 Sending generation request..."},
                )

                gen_resp = self.workflow_api.generate_image(
                    google_access_token=self.google_token,
                    workflow_id=self.workflow_id,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    image_model=task.get("model", "veo_3_1_t2v_fast"),
                    media_inputs=media_inputs or None,
                    timeout=self.api_timeout,
                    recaptcha_token=recaptcha_token,
                )

                if not gen_resp.success:
                    error_msg = gen_resp.message or "Generation failed"
                    raise Exception(error_msg)

                # Extract operation info for polling
                response_data = gen_resp.data.get("response", {})
                operations = response_data.get("operations", [])
                scene_id = gen_resp.data.get("scene_id", "")

                if not operations:
                    raise Exception("No operations in generation response")

                op = operations[0]
                operation_name = op.get("operation", {}).get("name", "")
                op_status = op.get("status", "MEDIA_GENERATION_STATUS_ACTIVE")

                if not operation_name:
                    raise Exception("No operation name in response")

                logger.info(f"🎬 Video generation started: op={operation_name}, scene={scene_id}")
                self.task_progress.emit(
                    task_id, 25, "running",
                    {
                        "upload_status": f"🎬 Generating video... (polling every {self.poll_interval}s)",
                        "operation_name": operation_name,
                        "scene_id": scene_id,
                    },
                )

                # Poll for video completion
                saved_path = self._poll_video_status(
                    task_id=task_id,
                    operation_name=operation_name,
                    scene_id=scene_id,
                    current_status=op_status,
                    output_folder=output_folder,
                    filename_prefix=filename_prefix,
                    stt=task.get("stt", 0),
                    img_idx=img_idx,
                    start_time=start_time,
                )
                if saved_path:
                    saved_paths.append(saved_path)

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

    def _get_save_folder(self, output_folder: str) -> str:
        """Compute the save folder path."""
        if output_folder:
            return output_folder
        base = os.path.join(os.path.expanduser("~"), "Downloads", "whisk_pro")
        if self.workflow_name:
            safe_wf = self.workflow_name.replace("/", "_").replace(":", "_").strip()
            if self.flow_name:
                safe_flow = self.flow_name.replace("/", "_").replace(":", "_").strip()
                folder_name = f"{safe_flow}_{safe_wf}"
            else:
                folder_name = safe_wf
            return os.path.join(base, folder_name)
        elif self.flow_name:
            safe_flow = self.flow_name.replace("/", "_").replace(":", "_").strip()
            return os.path.join(base, safe_flow)
        return base

    def _poll_video_status(
        self,
        task_id: str,
        operation_name: str,
        scene_id: str,
        current_status: str,
        output_folder: str,
        filename_prefix: str,
        stt: int,
        img_idx: int,
        start_time: float,
    ) -> str:
        """Poll video status until complete. Returns saved file path or empty."""
        poll_count = 0
        poll_start = time.time()

        while not self._stop_flag:
            elapsed_total = time.time() - start_time
            poll_elapsed = time.time() - poll_start

            if poll_elapsed >= self.POLL_MAX_TIME:
                raise TimeoutError(
                    f"Polling timeout ({int(poll_elapsed)}s). "
                    "Video chưa sẵn sàng sau thời gian chờ tối đa."
                )

            # Wait poll_interval between checks
            if poll_count > 0:
                for _ in range(self.poll_interval * 2):  # 0.5s ticks
                    if self._stop_flag:
                        return ""
                    time.sleep(0.5)

            poll_count += 1

            # Update progress (25-90% range during polling)
            pct = min(90, 25 + int((poll_elapsed / self.POLL_MAX_TIME) * 65))
            elapsed_min = int(poll_elapsed) // 60
            elapsed_sec = int(poll_elapsed) % 60
            self.task_progress.emit(
                task_id, pct, "running",
                {"upload_status": f"⏳ Polling #{poll_count} ({elapsed_min}m{elapsed_sec:02d}s)..."},
            )

            try:
                status_resp = self.workflow_api.check_video_status(
                    google_access_token=self.google_token,
                    operation_name=operation_name,
                    scene_id=scene_id,
                    current_status=current_status,
                )
            except Exception as e:
                logger.warning(f"⚠️ Poll #{poll_count} error: {e}")
                continue

            if not status_resp.success and "failed" in (status_resp.message or "").lower():
                raise Exception(status_resp.message)

            data = status_resp.data or {}
            new_status = data.get("status", "")

            if new_status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                fife_url = data.get("fife_url", "")
                if not fife_url:
                    raise Exception("Video completed but no download URL!")

                self.task_progress.emit(
                    task_id, 92, "running",
                    {"upload_status": "📥 Downloading video..."},
                )

                save_folder = self._get_save_folder(output_folder)
                saved_path = self._download_video(
                    url=fife_url,
                    save_folder=save_folder,
                    prefix=filename_prefix,
                    stt=stt,
                    img_idx=img_idx,
                )
                logger.info(f"💾 Video saved: {saved_path}")
                return saved_path

            elif new_status == "MEDIA_GENERATION_STATUS_FAILED":
                raise Exception("Video generation failed on server")

            # Update current_status for next poll
            current_status = new_status

        return ""

    @staticmethod
    def _download_video(
        url: str,
        save_folder: str,
        prefix: str,
        stt: int,
        img_idx: int,
    ) -> str:
        """Download video from URL and save to folder."""
        import urllib.request as urlreq

        os.makedirs(save_folder, exist_ok=True)

        parts = []
        if prefix:
            prefix = os.path.splitext(prefix)[0]
            parts.append(prefix)
        parts.append(f"{stt:03d}")
        if img_idx > 0:
            parts.append(f"{img_idx + 1}")
        filename = "_".join(parts) + ".mp4"
        filepath = os.path.join(save_folder, filename)

        req = urlreq.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/144.0.0.0 Safari/537.36",
        })
        with urlreq.urlopen(req, timeout=120) as resp:
            with open(filepath, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)

        logger.info(f"📥 Downloaded video ({os.path.getsize(filepath)} bytes): {filepath}")
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
