"""
Whisk Desktop — Queue Toolbar Widget.

Bottom toolbar with action buttons:
[Thêm dòng] [Xóa] [Xóa hết]
[Chạy lại lỗi] [Chạy mục chọn] [Tất cả]
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
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

    def retranslate(self):
        """Update tooltips when language changes."""
        self._add_row_btn.setToolTip(self.translator.t('toolbar.add_row'))
        self._delete_btn.setToolTip(self.translator.t('toolbar.delete'))
        self._delete_all_btn.setToolTip(self.translator.t('toolbar.delete_all'))
        self._download_all_btn.setToolTip(self.translator.t('toolbar.download_all'))
        self._retry_btn.setToolTip(self.translator.t('toolbar.retry_errors'))
        self._run_selected_btn.setToolTip(self.translator.t('toolbar.run_selected'))
        self._run_all_btn.setToolTip(self.translator.t('toolbar.run_all'))
