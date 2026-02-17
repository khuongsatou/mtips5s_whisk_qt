"""
Whisk Desktop — Task Queue Table Widget.

Custom QTableWidget for the image creation queue, matching
the reference: ☑ | STT | Task | Ref Images | Prompt | Output | Progress.
"""
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton, QCheckBox,
    QAbstractItemView, QSizePolicy, QProgressBar, QFrame,
)
from PySide6.QtCore import Signal, Qt, QTimer, QUrl
from PySide6.QtGui import QPixmap, QCursor, QDesktopServices
import os
import urllib.parse
from PySide6.QtWidgets import QApplication
from app.widgets.reference_image_grid import ReferenceImageGrid
from app.widgets.task_queue_table.helpers import (
    ClickableLabel, ImagePreviewDialog, PromptDelegate,
)


class TaskQueueTable(QTableWidget):
    """Queue table with columns matching the G-Labs reference."""

    PAGE_SIZE = 50  # Max items per page

    task_selected = Signal(list)     # Emits list of selected task IDs
    ref_images_changed = Signal(str, list)  # task_id, new paths
    download_clicked = Signal(str)   # task_id
    open_folder_clicked = Signal(str)  # task_id
    prompt_edited = Signal(str, str)  # task_id, new_prompt
    page_changed = Signal(int, int)  # current_page (1-based), total_pages
    stats_changed = Signal(int, int, int)  # completed, errors, total

    COLUMNS = [
        ("", 40),           # Checkbox
        ("STT", 55),        # Row number
        ("Task", 140),      # Task name + model + ratio
        ("ref_images", 420),  # Reference images grid (Title/Scene/Style)
        ("Prompt", -1),     # Prompt text (stretch)
        ("output", 200),    # Output thumbnails
        ("progress", 200),  # Progress bar + status + AI fix buttons
        ("message", 200),   # Error / info messages
        ("completed_at", 130),  # Completion timestamp
    ]

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.translator.language_changed.connect(self.retranslate)
        self._task_ids: list[str] = []  # IDs of visible (current page) rows
        self._checkboxes: dict[str, QCheckBox] = {}
        self._ref_grids: dict[str, ReferenceImageGrid] = {}
        self._all_tasks: list[dict] = []  # Full task list (all pages)
        self._current_page: int = 0  # 0-indexed
        self._search_text: str = ""
        self._status_filter: str = ""  # empty = all
        self._sort_done_at: str = "desc"  # "desc" (newest first), "asc" (oldest first)
        self.setObjectName("task_queue_table")
        self._setup_table()
        self.cellChanged.connect(self._on_cell_changed)

    def _setup_table(self):
        """Initialize table structure."""
        self.setColumnCount(len(self.COLUMNS))
        self._update_headers()
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setWordWrap(True)

        # Prevent table from expanding to fit all content — force scrolling
        self.setSizeAdjustPolicy(QAbstractItemView.AdjustIgnored)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Scroll policies
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Column sizing
        header = self.horizontalHeader()
        for i, (_, width) in enumerate(self.COLUMNS):
            if width == -1:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                self.setColumnWidth(i, width)

        # Ensure Prompt column has a reasonable minimum
        self.horizontalHeader().setMinimumSectionSize(50)
        self.setColumnWidth(4, max(250, self.columnWidth(4)))

        # Prompt column uses multi-line editor
        self.setItemDelegateForColumn(4, PromptDelegate(self))
        self.setEditTriggers(QAbstractItemView.DoubleClicked)

        # Clicking Prompt header copies all filtered prompts
        self.horizontalHeader().sectionClicked.connect(self._on_header_click)

    def _on_cell_changed(self, row: int, col: int):
        """Persist prompt edits to the API."""
        if col != 4:  # Only care about Prompt column
            return
        if row < 0 or row >= len(self._task_ids):
            return
        task_id = self._task_ids[row]
        item = self.item(row, col)
        if item:
            new_prompt = item.text().strip()
            self.prompt_edited.emit(task_id, new_prompt)

    def _update_headers(self):
        """Set column headers."""
        header_keys = [
            "", "queue.stt", "queue.task", "queue.ref_images",
            "queue.prompt", "queue.output", "queue.progress", "queue.message",
            "queue.completed_at",
        ]
        headers = []
        for idx, key in enumerate(header_keys):
            if key:
                label = self.translator.t(key)
                # Add copy icon to Prompt header
                if idx == 4:
                    label = f"📋 {label}"
                # Add sort icon to Done At header
                if idx == 8:
                    icon = "🔽" if self._sort_done_at == "desc" else "🔼"
                    label = f"{icon} {label}"
                headers.append(label)
            else:
                headers.append("")
        self.setHorizontalHeaderLabels(headers)

    def load_data(self, tasks: list[dict]):
        """Populate the table with task data using pagination + differential updates."""
        self._all_tasks = tasks

        # Sort: running first → completed_at (user-chosen direction) → pending last
        running = [t for t in tasks if t.get("status") == "running"]
        with_time = [t for t in tasks if t.get("status") != "running" and t.get("completed_at")]
        without_time = [t for t in tasks if t.get("status") != "running" and not t.get("completed_at")]
        is_desc = self._sort_done_at == "desc"
        with_time.sort(key=lambda t: t.get("completed_at", ""), reverse=is_desc)
        self._all_tasks = running + with_time + without_time

        filtered = self._get_filtered_tasks()

        # Clamp page to valid range
        total_pages = max(1, -(-len(filtered) // self.PAGE_SIZE))  # ceil division
        if self._current_page >= total_pages:
            self._current_page = total_pages - 1
        if self._current_page < 0:
            self._current_page = 0

        self._render_page()
        self.page_changed.emit(self._current_page + 1, total_pages)

        # Emit stats from unfiltered data
        completed = sum(1 for t in self._all_tasks if t.get("status") == "completed")
        errors = sum(1 for t in self._all_tasks if t.get("status") == "error")
        self.stats_changed.emit(completed, errors, len(self._all_tasks))

    def set_search_filter(self, text: str):
        """Set the search filter text and refresh the table."""
        self._search_text = text.strip().lower()
        self._current_page = 0
        self._current_data = None
        self.load_data(self._all_tasks)

    def set_status_filter(self, status: str):
        """Set the status filter and refresh the table."""
        self._status_filter = status
        self._current_page = 0
        self._current_data = None
        self.load_data(self._all_tasks)

    def _get_filtered_tasks(self) -> list[dict]:
        """Return tasks filtered by search text and status."""
        tasks = self._all_tasks
        if self._status_filter:
            tasks = [t for t in tasks if t.get("status") == self._status_filter]
        if self._search_text:
            tasks = [t for t in tasks if self._search_text in t.get("prompt", "").lower()]
        return tasks

    def _render_page(self):
        """Render the current page slice using differential updates."""
        filtered = self._get_filtered_tasks()
        start = self._current_page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_tasks = filtered[start:end]

        # Build lookup of incoming page tasks
        incoming = {t["id"]: t for t in page_tasks}
        incoming_order = [t["id"] for t in page_tasks]

        # First call or structure changed => full rebuild
        if not hasattr(self, '_current_data') or self._current_data is None:
            self._full_rebuild(page_tasks)
            return

        # Check if the set of task IDs or their order changed
        if incoming_order != self._task_ids:
            self._full_rebuild(page_tasks)
            return

        # Differential update — same rows, just update changed cells
        self.setUpdatesEnabled(False)
        scrollbar = self.verticalScrollBar()
        saved_scroll = scrollbar.value() if scrollbar else 0

        for row, task_id in enumerate(self._task_ids):
            old = self._current_data.get(task_id, {})
            new = incoming.get(task_id, {})
            if old == new:
                continue  # Nothing changed for this row

            # Update prompt if changed
            if old.get("prompt") != new.get("prompt"):
                self.blockSignals(True)
                prompt_item = self.item(row, 4)
                if prompt_item:
                    prompt_item.setText(new.get("prompt", ""))
                    prompt_item.setToolTip(new.get("prompt", ""))
                self.blockSignals(False)

            # Update output images if changed
            if old.get("output_images") != new.get("output_images"):
                self._update_output_cell(row, new)

            # Update progress/status if changed
            if (old.get("status") != new.get("status") or
                    old.get("progress") != new.get("progress") or
                    old.get("error_message") != new.get("error_message")):
                self._update_progress_cell(row, new)

            # Update error message column if changed
            if old.get("error_message") != new.get("error_message"):
                self._update_error_cell(row, new)

        # Cache current data
        self._current_data = {t["id"]: dict(t) for t in page_tasks}

        if scrollbar and saved_scroll > 0:
            scrollbar.setValue(saved_scroll)
        self.setUpdatesEnabled(True)

    # ── Pagination controls ───────────────────────────────────────────

    def next_page(self):
        """Go to next page if available."""
        total_pages = max(1, -(-len(self._all_tasks) // self.PAGE_SIZE))
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._current_data = None  # force full rebuild on page change
            self._render_page()
            self.page_changed.emit(self._current_page + 1, total_pages)

    def prev_page(self):
        """Go to previous page if available."""
        if self._current_page > 0:
            self._current_page -= 1
            self._current_data = None  # force full rebuild on page change
            self._render_page()
            total_pages = max(1, -(-len(self._all_tasks) // self.PAGE_SIZE))
            self.page_changed.emit(self._current_page + 1, total_pages)

    def go_to_page(self, page: int):
        """Go to a specific page (0-indexed)."""
        total_pages = max(1, -(-len(self._all_tasks) // self.PAGE_SIZE))
        page = max(0, min(page, total_pages - 1))
        if page != self._current_page:
            self._current_page = page
            self._current_data = None
            self._render_page()
            self.page_changed.emit(self._current_page + 1, total_pages)

    @property
    def total_items(self) -> int:
        """Total number of items across all pages."""
        return len(self._all_tasks)

    def _full_rebuild(self, tasks: list[dict]):
        """Full table rebuild — used on first load or when rows are added/removed."""
        scrollbar = self.verticalScrollBar()
        saved_scroll = scrollbar.value() if scrollbar else 0

        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        self.setRowCount(0)
        self._task_ids.clear()
        self._checkboxes.clear()
        self._ref_grids.clear()

        for row, task in enumerate(tasks):
            self.insertRow(row)
            self._build_row(row, task)

        self.blockSignals(False)

        # Cache current data
        self._current_data = {t["id"]: dict(t) for t in tasks}

        if scrollbar and saved_scroll > 0:
            scrollbar.setValue(saved_scroll)
        self.setUpdatesEnabled(True)

    def _build_row(self, row: int, task: dict):
        """Build all widgets for a single row."""
        task_id = task["id"]
        self._task_ids.append(task_id)

        # Set row height for ref image grid
        self.setRowHeight(row, 170)

        # Col 0: Checkbox
        cb_widget = QWidget()
        cb_layout = QHBoxLayout(cb_widget)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.setAlignment(Qt.AlignCenter)
        cb = QCheckBox()
        cb.setObjectName("queue_checkbox")
        cb.stateChanged.connect(lambda *a: self._emit_selection())
        cb_layout.addWidget(cb)
        self.setCellWidget(row, 0, cb_widget)
        self._checkboxes[task_id] = cb

        # Col 1: STT
        stt_item = QTableWidgetItem(str(task.get("stt", row + 1)))
        stt_item.setTextAlignment(Qt.AlignCenter)
        stt_item.setFlags(stt_item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, 1, stt_item)

        # Col 2: Task (name + model + ratio)
        task_cell = QWidget()
        task_layout = QVBoxLayout(task_cell)
        task_layout.setContentsMargins(8, 8, 8, 8)
        task_layout.setSpacing(3)

        task_name = QLabel(task.get("task_name", ""))
        task_name.setObjectName("task_name_label")
        task_name.setWordWrap(True)
        task_layout.addWidget(task_name)

        task_info = QLabel(f"{task.get('model', '')} |\n{task.get('aspect_ratio', '')}")
        task_info.setObjectName("task_info_label")
        task_info.setWordWrap(True)
        task_layout.addWidget(task_info)

        task_layout.addStretch()
        self.setCellWidget(row, 2, task_cell)

        # Col 3: Reference images grid
        ref_grid = ReferenceImageGrid()
        ref_by_cat = task.get("reference_images_by_cat")
        if ref_by_cat:
            ref_grid.set_paths_by_category(ref_by_cat)
        else:
            ref_images = task.get("reference_images", [])
            if ref_images:
                ref_grid.set_paths(ref_images)
        ref_grid.images_changed.connect(
            lambda paths, tid=task_id: self.ref_images_changed.emit(tid, paths)
        )
        self.setCellWidget(row, 3, ref_grid)
        self._ref_grids[task_id] = ref_grid

        # Col 4: Prompt (editable)
        prompt_text = task.get("prompt", "")
        prompt_item = QTableWidgetItem(prompt_text)
        prompt_item.setToolTip(prompt_text)
        self.setItem(row, 4, prompt_item)

        # Col 5: Output images
        self._update_output_cell(row, task)

        # Col 6: Progress
        self._update_progress_cell(row, task)

        # Col 7: Error message
        self._update_error_cell(row, task)

        # Col 8: Completed at
        self._update_completed_at_cell(row, task)

    def _update_output_cell(self, row: int, task: dict):
        """Update only the output images cell for a row."""
        output_widget = QWidget()
        output_layout = QGridLayout(output_widget)
        output_layout.setContentsMargins(4, 4, 4, 4)
        output_layout.setSpacing(4)

        output_images = task.get("output_images", [])
        num_outputs = task.get("images_per_prompt", 1)
        num_outputs = max(num_outputs, len(output_images), 1)
        thumb_size = 80 if num_outputs <= 2 else 44
        cols = 2
        for i in range(num_outputs):
            if i < len(output_images) and output_images[i]:
                img_path = output_images[i]
                thumb = ClickableLabel(img_path)
                thumb.setFixedSize(thumb_size, thumb_size)
                thumb.setAlignment(Qt.AlignCenter)
                pixmap = QPixmap(img_path).scaled(
                    thumb_size, thumb_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                thumb.setPixmap(pixmap)
                thumb.setToolTip("Click to preview")
                thumb.clicked.connect(self._show_image_preview)
            else:
                thumb = QLabel()
                thumb.setFixedSize(thumb_size, thumb_size)
                thumb.setAlignment(Qt.AlignCenter)
                thumb.setObjectName("output_placeholder")
                thumb.setText("🖼")
            output_layout.addWidget(thumb, i // cols, i % cols)
        self.setCellWidget(row, 5, output_widget)

    def _update_progress_cell(self, row: int, task: dict):
        """Update only the progress/status cell for a row."""
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(6, 6, 6, 6)
        progress_layout.setSpacing(4)
        progress_layout.setAlignment(Qt.AlignCenter)

        status = task.get("status", "pending")
        progress_pct = task.get("progress", 0)

        # Status badge
        status_label = QLabel()
        status_label.setAlignment(Qt.AlignCenter)
        if status == "completed":
            status_label.setText(self.translator.t("status.completed"))
            status_label.setObjectName("badge_completed")
        elif status == "running":
            status_label.setText(self.translator.t("status.running"))
            status_label.setObjectName("badge_running")
        elif status == "error":
            status_label.setText(self.translator.t("status.error"))
            status_label.setObjectName("badge_error")
            status_label.setToolTip(task.get("error_message", ""))
        else:
            status_label.setText(self.translator.t("status.pending"))
            status_label.setObjectName("badge_pending")
        progress_layout.addWidget(status_label)

        # Progress bar (shown for running & completed states)
        if status in ("running", "completed"):
            pbar = QProgressBar()
            pbar.setObjectName("task_progress_bar")
            pbar.setMinimum(0)
            pbar.setMaximum(100)
            pbar.setTextVisible(True)
            pbar.setFixedHeight(16)

            if status == "running":
                pbar.setValue(progress_pct)
                upload_status = task.get("upload_status", "")
                if upload_status:
                    pbar.setFormat(upload_status)
                else:
                    pbar.setFormat(f"{progress_pct}%  Processing…")
            else:
                pbar.setValue(100)
                pbar.setFormat("100%")
            progress_layout.addWidget(pbar)

        # Elapsed time label (running tasks only)
        if status == "running":
            elapsed_label = QLabel("⏱ 0s / 120s")
            elapsed_label.setObjectName("elapsed_timer_label")
            elapsed_label.setAlignment(Qt.AlignCenter)
            elapsed_label.setStyleSheet(
                "color: #9CA3AF; font-size: 11px; background: transparent;"
            )
            progress_layout.addWidget(elapsed_label)

        # Action buttons for completed tasks
        if status == "completed":
            task_id = self._task_ids[row] if row < len(self._task_ids) else ""
            action_row = QHBoxLayout()
            action_row.setSpacing(4)

            dl_btn = QPushButton("💾")
            dl_btn.setObjectName("action_icon_btn")
            dl_btn.setFixedSize(28, 28)
            dl_btn.setToolTip(self.translator.t("queue.download"))
            dl_btn.clicked.connect(
                lambda checked, tid=task_id: self.download_clicked.emit(tid)
            )
            action_row.addWidget(dl_btn)

            folder_btn = QPushButton("📂")
            folder_btn.setObjectName("action_icon_btn")
            folder_btn.setFixedSize(28, 28)
            folder_btn.setToolTip(self.translator.t("queue.open_folder"))
            folder_btn.clicked.connect(
                lambda checked, tid=task_id: self.open_folder_clicked.emit(tid)
            )
            action_row.addWidget(folder_btn)

            progress_layout.addLayout(action_row)

        # AI fix buttons for error tasks
        if status == "error":
            task_id = self._task_ids[row] if row < len(self._task_ids) else ""
            prompt = task.get("prompt", "")
            ai_row = QHBoxLayout()
            ai_row.setSpacing(4)

            gpt_btn = QPushButton("🤖 GPT")
            gpt_btn.setObjectName("action_icon_btn")
            gpt_btn.setFixedHeight(24)
            gpt_btn.setToolTip("Mở ChatGPT để sửa prompt")
            gpt_btn.setCursor(Qt.PointingHandCursor)
            gpt_btn.clicked.connect(
                lambda checked, p=prompt: self._open_ai_fix(p, "chatgpt")
            )
            ai_row.addWidget(gpt_btn)

            gemini_btn = QPushButton("✨ Gemini")
            gemini_btn.setObjectName("action_icon_btn")
            gemini_btn.setFixedHeight(24)
            gemini_btn.setToolTip("Mở Gemini để sửa prompt")
            gemini_btn.setCursor(Qt.PointingHandCursor)
            gemini_btn.clicked.connect(
                lambda checked, p=prompt: self._open_ai_fix(p, "gemini")
            )
            ai_row.addWidget(gemini_btn)

            progress_layout.addLayout(ai_row)

        self.setCellWidget(row, 6, progress_widget)

    def _update_error_cell(self, row: int, task: dict):
        """Update only the error message cell for a row."""
        error_msg = task.get("error_message", "")
        msg_label = QLabel(error_msg if error_msg else "")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        msg_label.setContentsMargins(6, 4, 6, 4)
        if error_msg:
            msg_label.setStyleSheet(
                "color: #EF4444; font-size: 12px; background: transparent;"
            )
            msg_label.setToolTip(error_msg)
        else:
            msg_label.setStyleSheet(
                "color: #9CA3AF; font-size: 12px; background: transparent;"
            )
        self.setCellWidget(row, 7, msg_label)

    def _update_completed_at_cell(self, row: int, task: dict):
        """Update the completed_at timestamp cell."""
        completed_at = task.get("completed_at", "")
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setContentsMargins(4, 4, 4, 4)
        if completed_at:
            # Format ISO string to readable time
            try:
                # completed_at is like "2026-02-16T21:30:00"
                from datetime import datetime
                dt = datetime.fromisoformat(completed_at)
                label.setText(dt.strftime("%H:%M:%S\n%d/%m"))
            except (ValueError, TypeError):
                label.setText(completed_at[:19])
            label.setStyleSheet(
                "color: #10B981; font-size: 11px; background: transparent;"
            )
        else:
            label.setText("—")
            label.setStyleSheet(
                "color: #6B7280; font-size: 11px; background: transparent;"
            )
        self.setCellWidget(row, 8, label)

    def _open_ai_fix(self, prompt: str, service: str):
        """Copy prompt + instruction to clipboard and open AI service."""
        instruction = (
            "Hãy kiểm tra prompt này có vi phạm chính sách không "
            "và sửa nó mà không làm thay đổi ngữ cảnh:\n\n"
        )
        full_text = instruction + prompt

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(full_text)

        # Open URL
        if service == "chatgpt":
            encoded = urllib.parse.quote(full_text, safe="")
            url = f"https://chatgpt.com/?prompt={encoded}"
        else:
            url = "https://gemini.google.com/"

        QDesktopServices.openUrl(QUrl(url))

    def _on_header_click(self, section: int):
        """Handle header click — Prompt column (4) copies, Done At (8) sorts."""
        if section == 4:  # Prompt column
            self._copy_all_prompts()
        elif section == 8:  # Done At column
            self._toggle_done_at_sort()

    def _toggle_done_at_sort(self):
        """Toggle sort direction for the Done At column and refresh."""
        self._sort_done_at = "asc" if self._sort_done_at == "desc" else "desc"
        self._current_data = None  # Force full rebuild
        self._update_headers()
        self.load_data(self._all_tasks)

    def _copy_all_prompts(self):
        """Copy all prompts (filtered) to clipboard."""
        filtered = self._get_filtered_tasks()
        prompts = [t.get("prompt", "") for t in filtered if t.get("prompt", "").strip()]
        if prompts:
            # If filtering error tasks, prepend policy check instruction
            if self._status_filter == "error":
                instruction = (
                    "Hãy kiểm tra prompt này có vi phạm chính sách không "
                    "và sửa nó mà không làm thay đổi ngữ cảnh:\n\n"
                )
                text = "\n---\n".join(instruction + p for p in prompts)
            else:
                text = "\n".join(prompts)
            QApplication.clipboard().setText(text)
            # Brief visual feedback via header label
            col_header = self.horizontalHeaderItem(4)
            original = col_header.text() if col_header else ""
            if col_header:
                col_header.setText(f"✅ Copied {len(prompts)}!")
                QTimer.singleShot(1500, lambda: col_header.setText(original))

    # ── Lightweight progress update (no full rebuild) ─────────────────

    def update_task_progress(self, task_id: str, progress: int, status: str,
                             error_message: str = "",
                             elapsed_seconds: int = 0,
                             upload_status: str = ""):
        """Update only the progress column for a specific task (no full rebuild)."""
        # Also update in the full task list cache for consistency
        for t in self._all_tasks:
            if t["id"] == task_id:
                t["status"] = status
                t["progress"] = progress
                if error_message:
                    t["error_message"] = error_message
                break

        # Only update UI if task is on current page
        if task_id not in self._task_ids:
            return
        row = self._task_ids.index(task_id)

        # Get or create the progress widget
        progress_widget = self.cellWidget(row, 6)
        if progress_widget is None:
            return

        layout = progress_widget.layout()
        if layout is None:
            return

        # Update status badge (first widget in layout)
        status_label = layout.itemAt(0)
        if status_label and status_label.widget():
            badge = status_label.widget()
            if status == "completed":
                badge.setText(self.translator.t("status.completed"))
                badge.setObjectName("badge_completed")
            elif status == "running":
                badge.setText(self.translator.t("status.running"))
                badge.setObjectName("badge_running")
            elif status == "error":
                badge.setText(self.translator.t("status.error"))
                badge.setObjectName("badge_error")
                badge.setToolTip(error_message)
            else:
                badge.setText(self.translator.t("status.pending"))
                badge.setObjectName("badge_pending")
            # Force style refresh after objectName change
            badge.style().unpolish(badge)
            badge.style().polish(badge)

        # Update or create progress bar
        pbar_item = layout.itemAt(1)
        pbar = pbar_item.widget() if pbar_item and isinstance(pbar_item.widget(), QProgressBar) else None

        if status in ("running", "completed") and pbar is None:
            # Create progress bar on-the-fly (task was initially "pending")
            pbar = QProgressBar()
            pbar.setObjectName("task_progress_bar")
            pbar.setMinimum(0)
            pbar.setMaximum(100)
            pbar.setTextVisible(True)
            pbar.setFixedHeight(16)
            layout.insertWidget(1, pbar)

        if pbar is not None:
            if status == "running":
                pbar.setValue(progress)
                if upload_status:
                    pbar.setFormat(upload_status)
                else:
                    pbar.setFormat(f"{progress}%  Processing…")
            elif status == "completed":
                pbar.setValue(100)
                pbar.setFormat("100%")

        # Update or create elapsed timer label
        if status == "running" and elapsed_seconds >= 0:
            timeout = 60
            # Find existing elapsed label or create one
            elapsed_label = None
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget() and item.widget().objectName() == "elapsed_timer_label":
                    elapsed_label = item.widget()
                    break
            if elapsed_label is None:
                elapsed_label = QLabel()
                elapsed_label.setObjectName("elapsed_timer_label")
                elapsed_label.setAlignment(Qt.AlignCenter)
                elapsed_label.setStyleSheet(
                    "color: #9CA3AF; font-size: 11px; background: transparent;"
                )
                # Insert after progress bar
                insert_idx = 2 if pbar is not None else 1
                layout.insertWidget(insert_idx, elapsed_label)
            remaining = max(0, timeout - elapsed_seconds)
            if elapsed_seconds >= timeout:
                elapsed_label.setText(f"⏱ {elapsed_seconds}s / {timeout}s ⚠️")
                elapsed_label.setStyleSheet(
                    "color: #EF4444; font-size: 11px; background: transparent;"
                )
            elif remaining <= 30:
                elapsed_label.setText(f"⏱ {elapsed_seconds}s / {timeout}s")
                elapsed_label.setStyleSheet(
                    "color: #F59E0B; font-size: 11px; background: transparent;"
                )
            else:
                elapsed_label.setText(f"⏱ {elapsed_seconds}s / {timeout}s")
                elapsed_label.setStyleSheet(
                    "color: #9CA3AF; font-size: 11px; background: transparent;"
                )

        # Update error message column
        msg_widget = self.cellWidget(row, 7)
        if msg_widget and isinstance(msg_widget, QLabel) and error_message:
            msg_widget.setText(error_message)
            msg_widget.setStyleSheet(
                "color: #EF4444; font-size: 12px; background: transparent;"
            )
            msg_widget.setToolTip(error_message)

    def _emit_selection(self):
        """Emit list of selected task IDs."""
        selected = []
        for task_id, cb in self._checkboxes.items():
            if cb.isChecked():
                selected.append(task_id)
        self.task_selected.emit(selected)

    def get_selected_ids(self) -> list[str]:
        """Return list of currently checked task IDs."""
        return [tid for tid, cb in self._checkboxes.items() if cb.isChecked()]

    def select_all(self, checked: bool = True):
        """Check or uncheck all rows."""
        for cb in self._checkboxes.values():
            cb.setChecked(checked)

    def select_errors(self):
        """Select only tasks with error status (on current page)."""
        error_ids = {
            t["id"] for t in self._all_tasks if t.get("status") == "error"
        }
        for task_id, cb in self._checkboxes.items():
            cb.setChecked(task_id in error_ids)

    def retranslate(self):
        """Update headers when language changes."""
        self._update_headers()

    def _show_image_preview(self, image_path: str):
        """Open image preview dialog for the given path."""
        dialog = ImagePreviewDialog(image_path, parent=self.window())
        dialog.exec()
