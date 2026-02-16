"""
Whisk Desktop — Task Queue Table Widget.

Custom QTableWidget for the image creation queue, matching
the reference: ☑ | STT | Task | Ref Images | Prompt | Output | Progress.
"""
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton, QCheckBox,
    QAbstractItemView, QSizePolicy, QProgressBar, QFrame,
    QStyledItemDelegate, QTextEdit, QDialog, QScrollArea, QFileDialog,
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QPixmap, QScreen, QCursor
import os
import shutil
from app.widgets.reference_image_grid import ReferenceImageGrid


class ClickableLabel(QLabel):
    """QLabel that emits a signal when clicked."""
    clicked = Signal(str)  # image_path

    def __init__(self, image_path: str = "", parent=None):
        super().__init__(parent)
        self._image_path = image_path
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._image_path:
            self.clicked.emit(self._image_path)
        super().mousePressEvent(event)


class ImagePreviewDialog(QDialog):
    """Modal dialog to preview an image at full size."""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Preview")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModal(True)
        self.setMinimumSize(480, 400)

        self._image_path = image_path

        # Get screen size for sensible dialog dimensions
        screen_size = self.screen().availableGeometry()
        max_w = int(screen_size.width() * 0.85)
        max_h = int(screen_size.height() * 0.85)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scrollable image area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setStyleSheet("background: #1a1a2e; border: none;")

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                max_w, max_h - 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            img_label.setPixmap(scaled)
        else:
            img_label.setText("Could not load image")
            img_label.setStyleSheet("color: #999; font-size: 16px;")

        scroll.setWidget(img_label)
        layout.addWidget(scroll, 1)

        # Bottom toolbar (solid background, no overlap)
        toolbar = QWidget()
        toolbar.setFixedHeight(52)
        toolbar.setStyleSheet("""
            QWidget {
                background: #2D2D44;
                border-top: 1px solid #3D3D5C;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(10)

        # Download button
        dl_btn = QPushButton("💾 Download")
        dl_btn.setCursor(Qt.PointingHandCursor)
        dl_btn.setFixedSize(140, 36)
        dl_btn.setStyleSheet("""
            QPushButton {
                background: #7C3AED;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background: #6D28D9; }
            QPushButton:pressed { background: #5B21B6; }
        """)
        dl_btn.clicked.connect(self._on_download)
        toolbar_layout.addWidget(dl_btn)

        toolbar_layout.addStretch()

        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(100, 36)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background: #DC2626; }
            QPushButton:pressed { background: #B91C1C; }
        """)
        close_btn.clicked.connect(self.close)
        toolbar_layout.addWidget(close_btn)

        layout.addWidget(toolbar)

        self.resize(min(pixmap.width() + 40, max_w), min(pixmap.height() + 100, max_h))

    def _on_download(self):
        """Save the previewed image to a user-chosen location."""
        if not self._image_path or not os.path.isfile(self._image_path):
            return
        basename = os.path.basename(self._image_path)
        default_path = os.path.join(os.path.expanduser("~/Downloads"), basename)
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save Image", default_path,
            "Images (*.png *.jpg *.jpeg *.webp);;All Files (*)",
        )
        if dest:
            shutil.copy2(self._image_path, dest)


class PromptDelegate(QStyledItemDelegate):
    """Custom delegate that uses a QTextEdit for multi-line prompt editing."""

    def createEditor(self, parent, option, index):
        editor = QTextEdit(parent)
        editor.setObjectName("prompt_editor")
        editor.setAcceptRichText(False)
        return editor

    def setEditorData(self, editor, index):
        text = index.data(Qt.DisplayRole) or ""
        editor.setPlainText(text)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.toPlainText(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class TaskQueueTable(QTableWidget):
    """Queue table with columns matching the G-Labs reference."""

    task_selected = Signal(list)     # Emits list of selected task IDs
    ref_images_changed = Signal(str, list)  # task_id, new paths
    download_clicked = Signal(str)   # task_id
    open_folder_clicked = Signal(str)  # task_id
    prompt_edited = Signal(str, str)  # task_id, new_prompt

    COLUMNS = [
        ("", 40),           # Checkbox
        ("STT", 44),        # Row number
        ("Task", 140),      # Task name + model + ratio
        ("ref_images", 420),  # Reference images grid (Title/Scene/Style)
        ("Prompt", -1),     # Prompt text (stretch)
        ("output", 200),    # Output thumbnails
        ("progress", 150),  # Progress bar + status
        ("message", 200),   # Error / info messages
    ]

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.translator.language_changed.connect(self.retranslate)
        self._task_ids: list[str] = []
        self._checkboxes: dict[str, QCheckBox] = {}
        self._ref_grids: dict[str, ReferenceImageGrid] = {}
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

        # Prompt column uses multi-line editor
        self.setItemDelegateForColumn(4, PromptDelegate(self))
        self.setEditTriggers(QAbstractItemView.DoubleClicked)

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
        ]
        headers = []
        for key in header_keys:
            if key:
                headers.append(self.translator.t(key))
            else:
                headers.append("")
        self.setHorizontalHeaderLabels(headers)

    def load_data(self, tasks: list[dict]):
        """Populate the table with task data."""
        # Preserve scroll position across rebuild
        scrollbar = self.verticalScrollBar()
        saved_scroll = scrollbar.value() if scrollbar else 0

        self.blockSignals(True)  # Prevent cellChanged during population
        self.setRowCount(0)
        self._task_ids.clear()
        self._checkboxes.clear()
        self._ref_grids.clear()

        for row, task in enumerate(tasks):
            self.insertRow(row)
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

            # Col 5: Output images (2-column grid, no overlap)
            output_widget = QWidget()
            output_layout = QGridLayout(output_widget)
            output_layout.setContentsMargins(4, 4, 4, 4)
            output_layout.setSpacing(4)

            output_images = task.get("output_images", [])
            num_outputs = task.get("images_per_prompt", 1)
            num_outputs = max(num_outputs, len(output_images), 1)
            # Scale thumb size based on count: 1-2 → 80px, 3-4 → 44px
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

            # Col 6: Progress bar + status badge + action buttons
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
                    pbar.setFormat(f"{progress_pct}%  Processing…")
                else:
                    pbar.setValue(100)
                    pbar.setFormat("100%")
                progress_layout.addWidget(pbar)

            # Action buttons for completed tasks
            if status == "completed":
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

            self.setCellWidget(row, 6, progress_widget)

            # Col 7: Message (error details)
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

        self.blockSignals(False)  # Re-enable cellChanged

        # Restore scroll position
        if scrollbar and saved_scroll > 0:
            scrollbar.setValue(saved_scroll)

    # ── Lightweight progress update (no full rebuild) ─────────────────

    def update_task_progress(self, task_id: str, progress: int, status: str,
                             error_message: str = ""):
        """Update only the progress column for a specific task (no full rebuild)."""
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
                pbar.setFormat(f"{progress}%  Processing…")
            elif status == "completed":
                pbar.setValue(100)
                pbar.setFormat("100%")

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

    def retranslate(self):
        """Update headers when language changes."""
        self._update_headers()

    def _show_image_preview(self, image_path: str):
        """Open image preview dialog for the given path."""
        dialog = ImagePreviewDialog(image_path, parent=self.window())
        dialog.exec()
