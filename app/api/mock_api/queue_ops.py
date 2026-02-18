"""
Whisk Desktop — Mock API Queue Operations.

Mixin class providing queue CRUD + execution operations.
"""
import json
import logging
import os
import uuid
from datetime import datetime

from app.api.models import ApiResponse, TaskItem

logger = logging.getLogger("whisk.mock_api")

CHECKPOINT_DIR = os.path.join(os.path.expanduser("~"), ".whisk_pro")


class QueueOpsMixin:
    """Mixin providing queue CRUD + execution operations for MockApi."""

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
            with open(self._checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}")

    def _load_checkpoint(self):
        """Load queue state from JSON checkpoint file on startup."""
        if not os.path.isfile(self._checkpoint_path):
            return
        try:
            with open(self._checkpoint_path, "r", encoding="utf-8") as f:
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
            if os.path.isfile(self._checkpoint_path):
                os.remove(self._checkpoint_path)
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
            model=data.get("model", "veo_3_1_t2v_fast"),
            aspect_ratio=data.get("aspect_ratio", "VIDEO_ASPECT_RATIO_LANDSCAPE"),
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
                            "output_folder", "filename_prefix", "completed_at"):
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
