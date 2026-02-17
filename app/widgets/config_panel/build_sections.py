"""
Whisk Desktop — Config Panel UI Build Methods.

Mixin class providing the _build_* methods for ConfigPanel sections.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QTextEdit, QPushButton, QLineEdit, QFrame,
    QCheckBox,
)
from PySide6.QtCore import Qt
from app.widgets.collapsible_section import CollapsibleSection


class BuildSectionsMixin:
    """Mixin providing _build_* methods for ConfigPanel UI sections."""

    def _build_pipeline_section(self, layout):
        """Build the 5-step pipeline indicator bar."""
        pipeline_widget = QWidget()
        pipeline_widget.setObjectName("pipeline_widget")
        pipeline_layout = QHBoxLayout(pipeline_widget)
        pipeline_layout.setContentsMargins(8, 8, 8, 8)
        pipeline_layout.setSpacing(0)

        self._pipeline_steps = []
        self._pipeline_circles = []
        self._pipeline_labels = []
        self._pipeline_active = 0
        steps = [
            ("1", "⚙️", "Config"),
            ("2", "💬", "Prompt"),
            ("3", "🖼️", "Reference"),
            ("4", "📁", "Output"),
            ("5", "▶️", "Run"),
        ]
        for i, (num, icon, label) in enumerate(steps):
            step = QWidget()
            step.setObjectName("pipeline_step")
            step_layout = QVBoxLayout(step)
            step_layout.setContentsMargins(4, 4, 4, 4)
            step_layout.setSpacing(2)
            step_layout.setAlignment(Qt.AlignCenter)

            circle = QLabel(num)
            circle.setObjectName("pipeline_step_circle")
            circle.setAlignment(Qt.AlignCenter)
            circle.setFixedSize(24, 24)
            step_layout.addWidget(circle, 0, Qt.AlignCenter)

            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setObjectName("pipeline_step_icon")
            step_layout.addWidget(icon_label)

            text_label = QLabel(label)
            text_label.setObjectName("pipeline_step_label")
            text_label.setAlignment(Qt.AlignCenter)
            step_layout.addWidget(text_label)

            pipeline_layout.addWidget(step, 1)
            self._pipeline_steps.append(step)
            self._pipeline_circles.append(circle)
            self._pipeline_labels.append(text_label)

            if i < len(steps) - 1:
                arrow = QLabel("→")
                arrow.setObjectName("pipeline_arrow")
                arrow.setAlignment(Qt.AlignCenter)
                pipeline_layout.addWidget(arrow)

        layout.addWidget(pipeline_widget)

    def _build_model_section(self, layout):
        """Build model, quality, and aspect ratio selector section."""
        self._model_section = CollapsibleSection(
            f"🎨 {self.translator.t('config.section_model')}", expanded=True
        )

        # New Workflow button
        workflow_row = QHBoxLayout()
        workflow_row.setSpacing(8)
        self._workflow_btn = QPushButton("🆕 New Workflow")
        self._workflow_btn.setObjectName("primary_button")
        self._workflow_btn.setCursor(Qt.PointingHandCursor)
        self._workflow_btn.clicked.connect(self.workflow_requested.emit)
        workflow_row.addWidget(self._workflow_btn)
        self._model_section.add_layout(workflow_row)

        # Workflow status label
        self._workflow_status = QLabel("")
        self._workflow_status.setObjectName("config_label")
        self._workflow_status.setWordWrap(True)
        self._workflow_status.setVisible(False)
        self._model_section.add_widget(self._workflow_status)

        # Model combo
        self._model_label = QLabel(f"🤖 {self.translator.t('config.model')}")
        self._model_label.setObjectName("config_label")
        self._model_section.add_widget(self._model_label)

        self._model_combo = QComboBox()
        self._model_combo.setObjectName("config_combo")
        for model in self.MODELS:
            self._model_combo.addItem(model, model)
        self._model_section.add_widget(self._model_combo)

        # Quality tier selector
        self._quality_label = QLabel(f"✨ {self.translator.t('config.quality')}")
        self._quality_label.setObjectName("config_label")
        self._model_section.add_widget(self._quality_label)

        quality_container = QWidget()
        quality_container.setObjectName("quality_container")
        quality_row = QHBoxLayout(quality_container)
        quality_row.setContentsMargins(0, 2, 0, 2)
        quality_row.setSpacing(6)

        self._quality_buttons: list[QPushButton] = []
        self._quality_values: list[str] = []

        quality_defs = [
            ("1K", "⭐", "Standard"),
            ("2K", "⭐⭐", "HD"),
            ("4K", "💎", "Ultra"),
        ]

        for value, icon, desc in quality_defs:
            btn = QPushButton()
            btn.setObjectName("ratio_option_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(56)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"{value} — {desc}")

            btn_layout = QVBoxLayout(btn)
            btn_layout.setContentsMargins(4, 6, 4, 4)
            btn_layout.setSpacing(2)
            btn_layout.setAlignment(Qt.AlignCenter)

            icon_label = QLabel(icon)
            icon_label.setObjectName("ratio_option_text")
            icon_label.setAlignment(Qt.AlignCenter)
            btn_layout.addWidget(icon_label, 0, Qt.AlignCenter)

            text_label = QLabel(desc)
            text_label.setObjectName("ratio_option_text")
            text_label.setAlignment(Qt.AlignCenter)
            btn_layout.addWidget(text_label, 0, Qt.AlignCenter)

            btn.clicked.connect(
                lambda checked, v=value: self._on_quality_selected(v)
            )
            quality_row.addWidget(btn)
            self._quality_buttons.append(btn)
            self._quality_values.append(value)

        self._selected_quality = "1K"
        self._quality_buttons[0].setChecked(True)
        # Disable HD and Ultra — not available yet
        for i, val in enumerate(self._quality_values):
            if val in ("2K", "4K"):
                self._quality_buttons[i].setEnabled(False)
        self._model_section.add_widget(quality_container)

        # Aspect ratio selector
        self._ratio_label = QLabel(f"📐 {self.translator.t('config.aspect_ratio')}")
        self._ratio_label.setObjectName("config_label")
        self._model_section.add_widget(self._ratio_label)

        ratio_container = QWidget()
        ratio_container.setObjectName("ratio_container")
        ratio_grid = QHBoxLayout(ratio_container)
        ratio_grid.setContentsMargins(0, 2, 0, 2)
        ratio_grid.setSpacing(6)

        self._ratio_buttons: list[QPushButton] = []
        self._ratio_values: list[str] = []

        ratio_defs = [
            ("16:9", "16:9", 16, 9),
            ("9:16", "9:16", 9, 16),
            ("1:1",  "1:1",  1, 1),
        ]

        for label, value, w_ratio, h_ratio in ratio_defs:
            btn = QPushButton()
            btn.setObjectName("ratio_option_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(64)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(label)

            btn_layout = QVBoxLayout(btn)
            btn_layout.setContentsMargins(4, 8, 4, 6)
            btn_layout.setSpacing(4)
            btn_layout.setAlignment(Qt.AlignCenter)

            shape = QFrame()
            shape.setObjectName("ratio_shape")
            max_dim = 30
            scale = min(max_dim / w_ratio, max_dim / h_ratio)
            shape_w = max(int(w_ratio * scale), 10)
            shape_h = max(int(h_ratio * scale), 10)
            shape.setFixedSize(shape_w, shape_h)
            btn_layout.addWidget(shape, 0, Qt.AlignCenter)

            text_label = QLabel(label)
            text_label.setObjectName("ratio_option_text")
            text_label.setAlignment(Qt.AlignCenter)
            btn_layout.addWidget(text_label, 0, Qt.AlignCenter)

            btn.clicked.connect(
                lambda checked, v=value: self._on_ratio_selected(v)
            )
            ratio_grid.addWidget(btn)
            self._ratio_buttons.append(btn)
            self._ratio_values.append(value)

        self._selected_ratio = "16:9"
        self._ratio_buttons[0].setChecked(True)
        self._model_section.add_widget(ratio_container)

        layout.addWidget(self._model_section)

    def _build_execution_section(self, layout):
        """Build execution settings: images/prompt, concurrency, delay."""
        self._exec_section = CollapsibleSection(
            f"⚙️ {self.translator.t('config.section_execution')}", expanded=True
        )

        # Images per prompt
        images_card = QWidget()
        images_card.setObjectName("exec_row_card")
        images_layout = QHBoxLayout(images_card)
        images_layout.setContentsMargins(10, 8, 10, 8)
        images_layout.setSpacing(8)

        images_icon = QLabel("🖼️")
        images_icon.setObjectName("exec_row_icon")
        images_icon.setFixedWidth(24)
        images_icon.setAlignment(Qt.AlignCenter)
        images_layout.addWidget(images_icon)

        self._images_label = QLabel(self.translator.t("config.images_per_prompt"))
        self._images_label.setObjectName("exec_row_label")
        images_layout.addWidget(self._images_label, 1)

        self._images_spin = QSpinBox()
        self._images_spin.setObjectName("config_spin")
        self._images_spin.setRange(1, 4)
        self._images_spin.setValue(1)
        self._images_spin.setFixedWidth(64)
        images_layout.addWidget(self._images_spin)
        self._exec_section.add_widget(images_card)

        # Concurrency
        conc_card = QWidget()
        conc_card.setObjectName("exec_row_card")
        conc_layout = QHBoxLayout(conc_card)
        conc_layout.setContentsMargins(10, 8, 10, 8)
        conc_layout.setSpacing(8)

        conc_icon = QLabel("⚡")
        conc_icon.setObjectName("exec_row_icon")
        conc_icon.setFixedWidth(24)
        conc_icon.setAlignment(Qt.AlignCenter)
        conc_layout.addWidget(conc_icon)

        self._concurrency_label = QLabel(self.translator.t("config.concurrency"))
        self._concurrency_label.setObjectName("exec_row_label")
        conc_layout.addWidget(self._concurrency_label, 1)

        self._concurrency_spin = QSpinBox()
        self._concurrency_spin.setObjectName("config_spin")
        self._concurrency_spin.setRange(1, 10)
        self._concurrency_spin.setValue(2)
        self._concurrency_spin.setFixedWidth(64)
        conc_layout.addWidget(self._concurrency_spin)
        self._exec_section.add_widget(conc_card)

        # Delay range
        delay_card = QWidget()
        delay_card.setObjectName("exec_row_card")
        delay_layout = QHBoxLayout(delay_card)
        delay_layout.setContentsMargins(10, 8, 10, 8)
        delay_layout.setSpacing(8)

        delay_icon = QLabel("⏱️")
        delay_icon.setObjectName("exec_row_icon")
        delay_icon.setFixedWidth(24)
        delay_icon.setAlignment(Qt.AlignCenter)
        delay_layout.addWidget(delay_icon)

        self._delay_label = QLabel(self.translator.t("config.delay"))
        self._delay_label.setObjectName("exec_row_label")
        delay_layout.addWidget(self._delay_label, 1)

        self._delay_min = QSpinBox()
        self._delay_min.setObjectName("config_spin")
        self._delay_min.setRange(0, 60)
        self._delay_min.setValue(10)
        self._delay_min.setSuffix("s")
        self._delay_min.setFixedWidth(72)
        delay_layout.addWidget(self._delay_min)

        arrow_label = QLabel("→")
        arrow_label.setObjectName("exec_row_label")
        arrow_label.setAlignment(Qt.AlignCenter)
        arrow_label.setFixedWidth(16)
        delay_layout.addWidget(arrow_label)

        self._delay_max = QSpinBox()
        self._delay_max.setObjectName("config_spin")
        self._delay_max.setRange(0, 120)
        self._delay_max.setValue(20)
        self._delay_max.setSuffix("s")
        self._delay_max.setFixedWidth(72)
        delay_layout.addWidget(self._delay_max)
        self._exec_section.add_widget(delay_card)

        # Auto-retry toggle
        auto_retry_card = QWidget()
        auto_retry_card.setObjectName("exec_row_card")
        auto_retry_layout = QHBoxLayout(auto_retry_card)
        auto_retry_layout.setContentsMargins(10, 8, 10, 8)
        auto_retry_layout.setSpacing(8)

        auto_retry_icon = QLabel("🔁")
        auto_retry_icon.setObjectName("exec_row_icon")
        auto_retry_icon.setFixedWidth(24)
        auto_retry_icon.setAlignment(Qt.AlignCenter)
        auto_retry_layout.addWidget(auto_retry_icon)

        self._auto_retry_cb = QCheckBox(self.translator.t("config.auto_retry"))
        self._auto_retry_cb.setObjectName("config_checkbox")
        self._auto_retry_cb.setChecked(False)
        auto_retry_layout.addWidget(self._auto_retry_cb, 1)
        self._exec_section.add_widget(auto_retry_card)

        layout.addWidget(self._exec_section)

    def _build_prompt_section(self, layout):
        """Build prompt input, file loader, and split mode section."""
        self._prompt_section = CollapsibleSection(
            f"✍️ {self.translator.t('config.section_prompt')}", expanded=True
        )

        # Load from file
        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self._file_btn = QPushButton(f"📄 {self.translator.t('config.load_file')}")
        self._file_btn.setObjectName("secondary_button")
        self._file_btn.clicked.connect(self._on_load_file)
        file_row.addWidget(self._file_btn)
        self._prompt_section.add_layout(file_row)

        # AI Prompt generator button
        ai_prompt_row = QHBoxLayout()
        ai_prompt_row.setSpacing(8)
        self._ai_prompt_btn = QPushButton(f"💡 {self.translator.t('prompt_gen.button')}")
        self._ai_prompt_btn.setObjectName("secondary_button")
        self._ai_prompt_btn.setCursor(Qt.PointingHandCursor)
        self._ai_prompt_btn.clicked.connect(self._on_open_prompt_generator)
        ai_prompt_row.addWidget(self._ai_prompt_btn)
        self._prompt_section.add_layout(ai_prompt_row)

        # Prompt
        self._prompt_label = QLabel(f"💬 {self.translator.t('config.prompt')}")
        self._prompt_label.setObjectName("config_label")
        self._prompt_section.add_widget(self._prompt_label)

        self._prompt_input = QTextEdit()
        self._prompt_input.setObjectName("config_prompt")
        self._prompt_input.setPlaceholderText(self.translator.t("config.prompt_placeholder"))
        self._prompt_input.setMinimumHeight(80)
        self._prompt_section.add_widget(self._prompt_input)

        # Prompt count label
        self._prompt_count_label = QLabel("")
        self._prompt_count_label.setObjectName("prompt_count_label")
        self._prompt_count_label.setAlignment(Qt.AlignRight)
        self._prompt_count_label.setStyleSheet(
            "color: #9CA3AF; font-size: 11px; background: transparent; padding: 0 4px;"
        )
        self._prompt_section.add_widget(self._prompt_count_label)

        # Split mode
        split_row = QHBoxLayout()
        split_row.setSpacing(6)

        self._split_label = QLabel("✂️ Split mode:")
        self._split_label.setObjectName("config_label")
        split_row.addWidget(self._split_label)

        self._split_combo = QComboBox()
        self._split_combo.setObjectName("config_combo")
        self._split_combo.addItem("🔍 Auto Detect", "auto")
        self._split_combo.addItem("↵ Single (\\n)", "single")
        self._split_combo.addItem("¶ Paragraph (\\n\\n)", "paragraph")
        self._split_combo.addItem("{ } JSON Prompt", "json")
        split_row.addWidget(self._split_combo, 1)
        self._prompt_section.add_layout(split_row)

        # Wire prompt count updates
        self._prompt_input.textChanged.connect(self._update_prompt_count)
        self._split_combo.currentIndexChanged.connect(self._update_prompt_count)

        layout.addWidget(self._prompt_section)

    def _build_output_section(self, layout):
        """Build output folder and filename prefix section."""
        self._output_section = CollapsibleSection(
            f"📁 {self.translator.t('config.section_output')}", expanded=False
        )

        # Filename prefix
        self._prefix_label = QLabel(f"🏷️ {self.translator.t('config.filename_prefix')}")
        self._prefix_label.setObjectName("config_label")
        self._output_section.add_widget(self._prefix_label)

        self._prefix_input = QLineEdit()
        self._prefix_input.setObjectName("config_path")
        self._prefix_input.setPlaceholderText("e.g. whisk_img_")
        self._prefix_input.setText("")
        self._output_section.add_widget(self._prefix_input)

        # Output folder
        self._output_label = QLabel(f"📂 {self.translator.t('config.output_folder')}")
        self._output_label.setObjectName("config_label")
        self._output_section.add_widget(self._output_label)

        output_row = QHBoxLayout()
        output_row.setSpacing(4)
        self._output_path = QLineEdit()
        self._output_path.setObjectName("config_path")
        self._output_path.setPlaceholderText("~/Downloads")
        self._output_path.setReadOnly(True)
        output_row.addWidget(self._output_path)

        self._output_browse = QPushButton("📂")
        self._output_browse.setObjectName("browse_button")
        self._output_browse.setFixedWidth(36)
        self._output_browse.clicked.connect(self._on_browse_output)
        output_row.addWidget(self._output_browse)
        self._output_section.add_layout(output_row)

        layout.addWidget(self._output_section)

    def _build_ref_images_section(self, layout):
        """Build reference images section with dynamic slot rows per category."""
        self._ref_section = CollapsibleSection(
            f"🖼️ {self.translator.t('config.section_ref_images')}", expanded=True
        )

        # --- Mode selector: toggle buttons ---
        mode_container = QWidget()
        mode_container.setObjectName("ref_mode_container")
        mode_layout = QHBoxLayout(mode_container)
        mode_layout.setContentsMargins(0, 4, 0, 4)
        mode_layout.setSpacing(6)

        self._ref_mode_btn_multi = QPushButton("📋 " + self.translator.t("config.ref_mode_multiple"))
        self._ref_mode_btn_multi.setCheckable(True)
        self._ref_mode_btn_multi.setChecked(False)
        self._ref_mode_btn_multi.setFixedHeight(36)
        self._ref_mode_btn_multi.setCursor(Qt.PointingHandCursor)
        self._ref_mode_btn_multi.clicked.connect(lambda: self._set_ref_mode("multiple"))
        mode_layout.addWidget(self._ref_mode_btn_multi, 1)

        self._ref_mode_btn_single = QPushButton("🔗 " + self.translator.t("config.ref_mode_single"))
        self._ref_mode_btn_single.setCheckable(True)
        self._ref_mode_btn_single.setChecked(True)
        self._ref_mode_btn_single.setFixedHeight(36)
        self._ref_mode_btn_single.setCursor(Qt.PointingHandCursor)
        self._ref_mode_btn_single.clicked.connect(lambda: self._set_ref_mode("single"))
        mode_layout.addWidget(self._ref_mode_btn_single, 1)

        self._current_ref_mode = "single"
        self._apply_ref_mode_styles()
        self._ref_section.add_widget(mode_container)

        # Pre-loaded media inputs for single mode (per category)
        self._preloaded_media_inputs = {"title": [], "scene": [], "style": []}

        # --- Category rows (with per-category Get ID) ---
        self._ref_slot_rows = {"title": [], "scene": [], "style": []}
        self._ref_containers = {}
        self._ref_add_btns = {}
        self._ref_getid_btns = {}
        self._ref_id_statuses = {}
        self._ref_getid_rows = {}

        categories = [
            ("title", "🎨", "config.ref_title"),
            ("scene", "🎬", "config.ref_scene"),
            ("style", "✨", "config.ref_style"),
        ]

        for cat_key, icon, trans_key in categories:
            label = QLabel(f"{icon} {self.translator.t(trans_key)}")
            label.setObjectName("config_label")
            self._ref_section.add_widget(label)
            setattr(self, f"_ref_{cat_key}_label", label)

            container_widget = QWidget()
            container_layout = QVBoxLayout(container_widget)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)
            self._ref_containers[cat_key] = container_layout

            self._add_ref_slot_row(cat_key)
            self._ref_section.add_widget(container_widget)

            add_btn = QPushButton("+ Add Slot")
            add_btn.setObjectName("ref_add_slot_btn")
            add_btn.setFixedHeight(22)
            add_btn.setCursor(Qt.PointingHandCursor)
            add_btn.clicked.connect(lambda checked, c=cat_key: self._add_ref_slot_row(c))
            self._ref_add_btns[cat_key] = add_btn
            self._ref_section.add_widget(add_btn)

            # Per-category Get ID button + status (single mode only)
            getid_row = QWidget()
            getid_lay = QHBoxLayout(getid_row)
            getid_lay.setContentsMargins(4, 4, 4, 4)
            getid_lay.setSpacing(8)

            # Category-specific colors and icons
            cat_styles = {
                "title": {"icon": "🎨", "bg": "#8e44ad", "hover": "#9b59b6", "border": "#7d3c98"},
                "scene": {"icon": "🎬", "bg": "#16a085", "hover": "#1abc9c", "border": "#138d75"},
                "style": {"icon": "✨", "bg": "#e67e22", "hover": "#f39c12", "border": "#d35400"},
            }
            cs = cat_styles.get(cat_key, cat_styles["title"])

            getid_btn = QPushButton(f"{cs['icon']} Get ID")
            getid_btn.setObjectName("ref_getid_btn")
            getid_btn.setFixedHeight(30)
            getid_btn.setMinimumWidth(100)
            getid_btn.setCursor(Qt.PointingHandCursor)
            getid_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {cs['bg']}, stop:1 {cs['hover']});
                    color: white;
                    border: 1px solid {cs['border']};
                    border-radius: 14px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 4px 16px;
                    letter-spacing: 0.5px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {cs['hover']}, stop:1 {cs['bg']});
                    border-color: {cs['hover']};
                }}
                QPushButton:pressed {{
                    background: {cs['border']};
                }}
                QPushButton:disabled {{
                    background: #95a5a6;
                    border-color: #7f8c8d;
                    color: #ecf0f1;
                }}
            """)
            getid_btn.clicked.connect(lambda checked, c=cat_key: self._on_get_ref_id(c))
            getid_lay.addWidget(getid_btn)

            id_status = QLabel("")
            id_status.setObjectName("ref_id_status")
            id_status.setStyleSheet(
                "QLabel { font-size: 11px; color: #7f8c8d; padding: 2px 4px; }"
            )
            getid_lay.addWidget(id_status, 1)

            getid_row.setVisible(False)  # Hidden in multiple mode
            self._ref_getid_btns[cat_key] = getid_btn
            self._ref_id_statuses[cat_key] = id_status
            self._ref_getid_rows[cat_key] = getid_row
            self._ref_section.add_widget(getid_row)

        layout.addWidget(self._ref_section)
