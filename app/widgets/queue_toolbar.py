"""
Whisk Desktop — Queue Toolbar Widget.

Bottom toolbar with action buttons:
[Thêm dòng] [Xóa] [Xóa hết]
[◀ Prev] [Page 1/3] [Next ▶]
[Chạy lại lỗi] [Chạy mục chọn] [Tất cả]
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt


class QueueToolbar(QWidget):
    """Bottom toolbar for queue management actions."""

    add_row = Signal()
    delete_selected = Signal()
    delete_all = Signal()
    clear_checkpoint = Signal()
    retry_errors = Signal()
    run_selected = Signal()
    run_all = Signal()
    download_all = Signal()
    prev_page = Signal()
    next_page = Signal()
    search_changed = Signal(str)
    status_filter_changed = Signal(str)
    select_errors = Signal()
    cancel_running = Signal()

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.translator.language_changed.connect(self.retranslate)
        self.setObjectName("queue_toolbar")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # --- Left group: data management ---
        self._add_row_btn = QPushButton("➕")
        self._add_row_btn.setObjectName("toolbar_button")
        self._add_row_btn.setCursor(Qt.PointingHandCursor)
        self._add_row_btn.setToolTip(self.translator.t('toolbar.add_row'))
        self._add_row_btn.clicked.connect(self.add_row.emit)
        layout.addWidget(self._add_row_btn)

        self._delete_btn = QPushButton("🗑")
        self._delete_btn.setObjectName("toolbar_danger_button")
        self._delete_btn.setCursor(Qt.PointingHandCursor)
        self._delete_btn.setToolTip(self.translator.t('toolbar.delete'))
        self._delete_btn.clicked.connect(self.delete_selected.emit)
        layout.addWidget(self._delete_btn)

        self._delete_all_btn = QPushButton("✖")
        self._delete_all_btn.setObjectName("toolbar_danger_button")
        self._delete_all_btn.setCursor(Qt.PointingHandCursor)
        self._delete_all_btn.setToolTip(self.translator.t('toolbar.delete_all'))
        self._delete_all_btn.clicked.connect(self.delete_all.emit)
        layout.addWidget(self._delete_all_btn)

        self._clear_ckpt_btn = QPushButton("🧹")
        self._clear_ckpt_btn.setObjectName("toolbar_danger_button")
        self._clear_ckpt_btn.setCursor(Qt.PointingHandCursor)
        self._clear_ckpt_btn.setToolTip("Clear Checkpoint")
        self._clear_ckpt_btn.clicked.connect(self.clear_checkpoint.emit)
        layout.addWidget(self._clear_ckpt_btn)

        self._select_errors_btn = QPushButton("⚠️")
        self._select_errors_btn.setObjectName("toolbar_button")
        self._select_errors_btn.setCursor(Qt.PointingHandCursor)
        self._select_errors_btn.setToolTip(self.translator.t('toolbar.select_errors'))
        self._select_errors_btn.clicked.connect(self.select_errors.emit)
        layout.addWidget(self._select_errors_btn)

        self._cancel_running_btn = QPushButton("⏹")
        self._cancel_running_btn.setObjectName("toolbar_danger_button")
        self._cancel_running_btn.setCursor(Qt.PointingHandCursor)
        self._cancel_running_btn.setToolTip(self.translator.t('toolbar.cancel_running'))
        self._cancel_running_btn.clicked.connect(self.cancel_running.emit)
        layout.addWidget(self._cancel_running_btn)

        layout.addStretch()

        # --- Stats label ---
        self._stats_label = QLabel("")
        self._stats_label.setObjectName("stats_label")
        self._stats_label.setAlignment(Qt.AlignCenter)
        self._stats_label.setStyleSheet(
            "font-size: 12px; color: #9CA3AF; background: transparent; padding: 0 8px;"
        )
        layout.addWidget(self._stats_label)


        # --- Center group: pagination ---
        self._prev_page_btn = QPushButton("◀")
        self._prev_page_btn.setObjectName("toolbar_button")
        self._prev_page_btn.setCursor(Qt.PointingHandCursor)
        self._prev_page_btn.setToolTip(self.translator.t('toolbar.prev_page'))
        self._prev_page_btn.setFixedWidth(36)
        self._prev_page_btn.clicked.connect(self.prev_page.emit)
        layout.addWidget(self._prev_page_btn)

        self._page_label = QLabel("1 / 1")
        self._page_label.setObjectName("page_label")
        self._page_label.setAlignment(Qt.AlignCenter)
        self._page_label.setFixedWidth(60)
        layout.addWidget(self._page_label)

        self._next_page_btn = QPushButton("▶")
        self._next_page_btn.setObjectName("toolbar_button")
        self._next_page_btn.setCursor(Qt.PointingHandCursor)
        self._next_page_btn.setToolTip(self.translator.t('toolbar.next_page'))
        self._next_page_btn.setFixedWidth(36)
        self._next_page_btn.clicked.connect(self.next_page.emit)
        layout.addWidget(self._next_page_btn)

        layout.addStretch()

        # --- Right group: execution ---
        self._download_all_btn = QPushButton("📥")
        self._download_all_btn.setObjectName("toolbar_button")
        self._download_all_btn.setCursor(Qt.PointingHandCursor)
        self._download_all_btn.setToolTip(self.translator.t('toolbar.download_all'))
        self._download_all_btn.clicked.connect(self.download_all.emit)
        layout.addWidget(self._download_all_btn)

        self._retry_btn = QPushButton("🔄")
        self._retry_btn.setObjectName("toolbar_button")
        self._retry_btn.setCursor(Qt.PointingHandCursor)
        self._retry_btn.setToolTip(self.translator.t('toolbar.retry_errors'))
        self._retry_btn.clicked.connect(self.retry_errors.emit)
        layout.addWidget(self._retry_btn)

        self._run_selected_btn = QPushButton("▶")
        self._run_selected_btn.setObjectName("toolbar_run_button")
        self._run_selected_btn.setCursor(Qt.PointingHandCursor)
        self._run_selected_btn.setToolTip(self.translator.t('toolbar.run_selected'))
        self._run_selected_btn.clicked.connect(self.run_selected.emit)
        layout.addWidget(self._run_selected_btn)

        self._run_all_btn = QPushButton("⏩")
        self._run_all_btn.setObjectName("toolbar_run_button")
        self._run_all_btn.setCursor(Qt.PointingHandCursor)
        self._run_all_btn.setToolTip(self.translator.t('toolbar.run_all'))
        self._run_all_btn.clicked.connect(self.run_all.emit)
        layout.addWidget(self._run_all_btn)

    def update_page_info(self, current_page: int, total_pages: int):
        """Update the page label and enable/disable prev/next buttons."""
        self._page_label.setText(f"{current_page} / {total_pages}")
        self._prev_page_btn.setEnabled(current_page > 1)
        self._next_page_btn.setEnabled(current_page < total_pages)

    def update_stats(self, completed: int, errors: int, total: int):
        """Update the stats label with task counts."""
        self._stats_label.setText(
            f"✅ {completed}  ❌ {errors}  📋 {total}"
        )

    def retranslate(self):
        """Update tooltips when language changes."""
        self._add_row_btn.setToolTip(self.translator.t('toolbar.add_row'))
        self._delete_btn.setToolTip(self.translator.t('toolbar.delete'))
        self._delete_all_btn.setToolTip(self.translator.t('toolbar.delete_all'))
        self._select_errors_btn.setToolTip(self.translator.t('toolbar.select_errors'))
        self._download_all_btn.setToolTip(self.translator.t('toolbar.download_all'))
        self._retry_btn.setToolTip(self.translator.t('toolbar.retry_errors'))
        self._run_selected_btn.setToolTip(self.translator.t('toolbar.run_selected'))
        self._run_all_btn.setToolTip(self.translator.t('toolbar.run_all'))
        self._prev_page_btn.setToolTip(self.translator.t('toolbar.prev_page'))
        self._next_page_btn.setToolTip(self.translator.t('toolbar.next_page'))
        self._cancel_running_btn.setToolTip(self.translator.t('toolbar.cancel_running'))


