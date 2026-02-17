"""
Whisk Desktop — Configuration Panel Widget.

Left-side panel for image generation settings: model, quality,
aspect ratio, prompt, folder pickers, and "Add to Queue" button.
Uses CollapsibleSection for grouping related settings.

The ConfigPanel class composes functionality from two mixins:
- BuildSectionsMixin: _build_* methods for each UI section
- SettingsHandlersMixin: settings, events, pipeline, retranslate
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea,
)
from PySide6.QtCore import Signal, Qt
from app.widgets.config_panel.build_sections import BuildSectionsMixin
from app.widgets.config_panel.settings_handlers import SettingsHandlersMixin


class ConfigPanel(BuildSectionsMixin, SettingsHandlersMixin, QWidget):
    """Left-side configuration panel for image generation."""

    add_to_queue = Signal(dict)  # Emits config dict
    ref_images_picked = Signal(str, int, list)  # category, slot_index (0-based), list of paths
    workflow_requested = Signal()  # Emits when user clicks New Workflow
    request_upload_ref = Signal(str, dict)  # (category, {category: [paths]}) for pre-upload

    MODELS = ["IMAGEN_3_5"]
    RATIOS = [
        ("16:9 Ngang", "16:9"),
        ("9:16 Dọc", "9:16"),
        ("1:1 Vuông", "1:1"),
        ("4:3", "4:3"),
    ]

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.translator.language_changed.connect(self.retranslate)
        self.setObjectName("config_panel")
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("config_scroll")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Section title
        self._section_title = QLabel(self.translator.t("config.title"))
        self._section_title.setObjectName("config_section_title")
        layout.addWidget(self._section_title)

        # Build each section via dedicated methods (from BuildSectionsMixin)
        self._build_pipeline_section(layout)
        self._build_model_section(layout)
        self._build_execution_section(layout)
        self._build_prompt_section(layout)
        self._build_output_section(layout)
        self._build_ref_images_section(layout)

        layout.addStretch()

        # --- Buttons row ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._add_btn = QPushButton(f"➕ {self.translator.t('config.add_to_queue')}")
        self._add_btn.setObjectName("primary_button")
        self._add_btn.setEnabled(False)  # Disabled until workflow is linked
        self._add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(self._add_btn, 2)

        self._reset_btn = QPushButton("🔄 Reset")
        self._reset_btn.setObjectName("secondary_button")
        self._reset_btn.setFixedWidth(90)
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.clicked.connect(self.reset_to_defaults)
        btn_row.addWidget(self._reset_btn)

        layout.addLayout(btn_row)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Connect pipeline auto-activation (from SettingsHandlersMixin)
        self._connect_pipeline_signals()
        self.set_pipeline_step(0)  # Config already set by default

        # Load saved settings (from SettingsHandlersMixin)
        self._load_settings()
