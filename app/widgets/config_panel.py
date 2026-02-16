"""
Whisk Desktop — Configuration Panel Widget.

Left-side panel for image generation settings: model, quality,
aspect ratio, prompt, folder pickers, and "Add to Queue" button.
Uses CollapsibleSection for grouping related settings.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QRadioButton, QButtonGroup, QSpinBox, QTextEdit,
    QPushButton, QLineEdit, QFileDialog, QFrame, QScrollArea,
)
from PySide6.QtCore import Signal, Qt, QSettings
from app.widgets.collapsible_section import CollapsibleSection


class ConfigPanel(QWidget):
    """Left-side configuration panel for image generation."""

    add_to_queue = Signal(dict)  # Emits config dict
    ref_images_picked = Signal(str, int, list)  # category, slot_index (0-based), list of paths
    workflow_requested = Signal()  # Emits when user clicks New Workflow

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

        # Build each section via dedicated methods
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

        # Connect pipeline auto-activation
        self._connect_pipeline_signals()
        self.set_pipeline_step(0)  # Config already set by default

        # Load saved settings
        self._load_settings()

    # ═══════════════════════════════════════════════════
    # Build methods — each creates one UI section
    # ═══════════════════════════════════════════════════

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
            ("4:3",  "4:3",  4, 3),
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

        # Prompt
        self._prompt_label = QLabel(f"💬 {self.translator.t('config.prompt')}")
        self._prompt_label.setObjectName("config_label")
        self._prompt_section.add_widget(self._prompt_label)

        self._prompt_input = QTextEdit()
        self._prompt_input.setObjectName("config_prompt")
        self._prompt_input.setPlaceholderText(self.translator.t("config.prompt_placeholder"))
        self._prompt_input.setMinimumHeight(80)
        self._prompt_section.add_widget(self._prompt_input)

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

        self._ref_slot_rows = {"title": [], "scene": [], "style": []}
        self._ref_containers = {}
        self._ref_add_btns = {}

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

        layout.addWidget(self._ref_section)

    def _on_load_file(self):
        """Open file dialog to load prompts from TXT/Excel."""
        path, _ = QFileDialog.getOpenFileName(
            self, self.translator.t("config.load_file"),
            "", "Text Files (*.txt);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._prompt_input.setPlainText(f.read())
            except Exception:
                pass

    def _on_browse_output(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, self.translator.t("config.output_folder")
        )
        if folder:
            self._output_path.setText(folder)

    _IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tiff *.tif);;All Files (*)"

    def _add_ref_slot_row(self, category: str):
        """Add a new slot row for a category (max 5)."""
        rows = self._ref_slot_rows[category]
        if len(rows) >= 5:
            return

        slot_idx = len(rows)  # 0-based
        row_layout = QHBoxLayout()
        row_layout.setSpacing(4)

        # Slot label
        slot_label = QLabel(f"Slot {slot_idx + 1}")
        slot_label.setObjectName("config_label")
        slot_label.setFixedWidth(45)
        row_layout.addWidget(slot_label)

        # Path input
        path_input = QLineEdit()
        path_input.setObjectName("config_path")
        path_input.setPlaceholderText("Select images...")
        path_input.setReadOnly(True)
        row_layout.addWidget(path_input)

        # Browse button
        browse_btn = QPushButton("📂")
        browse_btn.setObjectName("browse_button")
        browse_btn.setFixedWidth(36)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(
            lambda checked, c=category, s=slot_idx, p=path_input: self._on_browse_ref_slot(c, s, p)
        )
        row_layout.addWidget(browse_btn)

        self._ref_containers[category].addLayout(row_layout)
        rows.append({"layout": row_layout, "path_input": path_input, "slot_idx": slot_idx})

        # Hide add button if max reached
        if len(rows) >= 5:
            self._ref_add_btns[category].hide()

    def _on_browse_ref_slot(self, category: str, slot_idx: int, path_input: QLineEdit):
        """Pick images for a specific slot of a category."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, f"Select {category.capitalize()} Slot {slot_idx + 1} images",
            "", self._IMAGE_FILTER
        )
        if not paths:
            return

        path_input.setText(f"{len(paths)} images selected")

        # Store selected paths
        if not hasattr(self, '_ref_images'):
            self._ref_images = {}
        # Key: "category_slotN"
        self._ref_images[f"{category}_{slot_idx}"] = paths

        # Emit signal so table auto-populates
        self.ref_images_picked.emit(category, slot_idx, paths)

    def _on_add(self):
        """Emit add_to_queue signal with current config."""
        # Collect all ref images per category
        ref_images = getattr(self, '_ref_images', {})
        ref_by_cat = {}
        for cat in ("title", "scene", "style"):
            cat_images = []
            for slot_row in self._ref_slot_rows.get(cat, []):
                idx = slot_row["slot_idx"]
                cat_images.extend(ref_images.get(f"{cat}_{idx}", []))
            ref_by_cat[cat] = cat_images

        config = {
            "model": self._model_combo.currentData(),
            "quality": self._selected_quality,
            "aspect_ratio": self._selected_ratio,
            "images_per_prompt": self._images_spin.value(),
            "concurrency": self._concurrency_spin.value(),
            "delay_min": self._delay_min.value(),
            "delay_max": self._delay_max.value(),
            "prompt": self._prompt_input.toPlainText().strip(),
            "split_mode": self._split_combo.currentData(),
            "filename_prefix": self._prefix_input.text().strip(),
            "output_folder": self._output_path.text(),
            "ref_title_images": ref_by_cat.get("title", []),
            "ref_scene_images": ref_by_cat.get("scene", []),
            "ref_style_images": ref_by_cat.get("style", []),
        }
        self.add_to_queue.emit(config)

        # Save settings (keep config values) then clear prompt + refs
        self._save_settings()
        self.clear_inputs()

    # --- Persistence ---

    def _save_settings(self):
        """Save current config values to QSettings."""
        s = QSettings("Whisk", "ConfigPanel")
        s.setValue("model", self._model_combo.currentData())
        s.setValue("quality", self._selected_quality)
        s.setValue("aspect_ratio", self._selected_ratio)
        s.setValue("images_per_prompt", self._images_spin.value())
        s.setValue("concurrency", self._concurrency_spin.value())
        s.setValue("delay_min", self._delay_min.value())
        s.setValue("delay_max", self._delay_max.value())
        s.setValue("split_mode", self._split_combo.currentData())
        s.setValue("filename_prefix", self._prefix_input.text().strip())
        s.setValue("output_folder", self._output_path.text())

    def _load_settings(self):
        """Load saved config values from QSettings."""
        s = QSettings("Whisk", "ConfigPanel")

        # Model
        model = s.value("model")
        if model:
            idx = self._model_combo.findData(model)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)

        # Quality
        quality = s.value("quality")
        if quality and quality in ("1K", "2K", "4K"):
            self._selected_quality = quality
            for i, val in enumerate(self._quality_values):
                if val == quality:
                    self._quality_buttons[i].setChecked(True)
                    break

        # Aspect ratio
        ratio = s.value("aspect_ratio")
        if ratio:
            self._selected_ratio = ratio
            for i, val in enumerate(self._ratio_values):
                if val == ratio:
                    self._ratio_buttons[i].setChecked(True)
                    break

        # Spinners
        ipp = s.value("images_per_prompt", type=int)
        if ipp:
            self._images_spin.setValue(ipp)
        conc = s.value("concurrency", type=int)
        if conc:
            self._concurrency_spin.setValue(conc)
        dmin = s.value("delay_min", type=int)
        if s.contains("delay_min"):
            self._delay_min.setValue(dmin)
        dmax = s.value("delay_max", type=int)
        if s.contains("delay_max"):
            self._delay_max.setValue(dmax)

        # Split mode
        split = s.value("split_mode")
        if split:
            idx = self._split_combo.findData(split)
            if idx >= 0:
                self._split_combo.setCurrentIndex(idx)

        # Prefix & output
        prefix = s.value("filename_prefix", "")
        if prefix and "{{" not in prefix:
            self._prefix_input.setText(prefix)
        output = s.value("output_folder", "")
        if output:
            self._output_path.setText(output)

    def clear_inputs(self):
        """Clear prompt and reference images (keep other config)."""
        self._prompt_input.clear()
        self._ref_images = {}
        for cat in ("title", "scene", "style"):
            for row in self._ref_slot_rows.get(cat, []):
                row["path_input"].clear()

    def reset_to_defaults(self):
        """Reset all settings to factory defaults."""
        # Model
        self._model_combo.setCurrentIndex(0)
        # Quality
        self._selected_quality = "1K"
        for i, val in enumerate(self._quality_values):
            self._quality_buttons[i].setChecked(val == "1K")
        # Aspect ratio
        self._selected_ratio = "16:9"
        for i, val in enumerate(self._ratio_values):
            if val == "16:9":
                self._ratio_buttons[i].setChecked(True)
                break
        # Spinners
        self._images_spin.setValue(1)
        self._concurrency_spin.setValue(1)
        self._delay_min.setValue(3)
        self._delay_max.setValue(5)
        # Split mode
        self._split_combo.setCurrentIndex(0)
        # Clear text fields
        self._prefix_input.clear()
        self._output_path.clear()
        self._prompt_input.clear()
        # Clear ref images
        self._ref_images = {}
        for cat in ("title", "scene", "style"):
            for row in self._ref_slot_rows.get(cat, []):
                row["path_input"].clear()
        # Clear saved settings
        QSettings("Whisk", "ConfigPanel").clear()

    def retranslate(self):
        """Update all labels when language changes."""
        self._section_title.setText(self.translator.t("config.title"))
        self._model_section.set_title(f"🎨 {self.translator.t('config.section_model')}")
        self._exec_section.set_title(f"⚙️ {self.translator.t('config.section_execution')}")
        self._prompt_section.set_title(f"✍️ {self.translator.t('config.section_prompt')}")
        self._output_section.set_title(f"📁 {self.translator.t('config.section_output')}")
        self._model_label.setText(f"🤖 {self.translator.t('config.model')}")
        self._quality_label.setText(f"✨ {self.translator.t('config.quality')}")
        self._ratio_label.setText(f"📐 {self.translator.t('config.aspect_ratio')}")
        self._images_label.setText(self.translator.t('config.images_per_prompt'))
        self._concurrency_label.setText(self.translator.t('config.concurrency'))
        self._delay_label.setText(self.translator.t('config.delay'))
        self._file_btn.setText(f"📄 {self.translator.t('config.load_file')}")
        self._prompt_label.setText(f"💬 {self.translator.t('config.prompt')}")
        self._prompt_input.setPlaceholderText(self.translator.t("config.prompt_placeholder"))
        self._prefix_label.setText(f"🏷️ {self.translator.t('config.filename_prefix')}")
        self._output_label.setText(f"📂 {self.translator.t('config.output_folder')}")
        self._ref_section.set_title(f"🖼️ {self.translator.t('config.section_ref_images')}")
        self._ref_title_label.setText(f"🎨 {self.translator.t('config.ref_title')}")
        self._ref_scene_label.setText(f"🎬 {self.translator.t('config.ref_scene')}")
        self._ref_style_label.setText(f"✨ {self.translator.t('config.ref_style')}")
        self._add_btn.setText(f"➕ {self.translator.t('config.add_to_queue')}")

    def set_workflow_status(self, text: str, error: bool = False):
        """Update the workflow status label below the New Workflow button."""
        self._workflow_status.setText(text)
        self._workflow_status.setStyleSheet(
            "color: #e74c3c; padding: 4px;" if error
            else "color: #27ae60; padding: 4px;"
        )
        self._workflow_status.setVisible(bool(text))

    def set_workflow_btn_enabled(self, enabled: bool):
        """Enable/disable the New Workflow button."""
        self._workflow_btn.setEnabled(enabled)

    def _on_ratio_selected(self, value: str):
        """Handle aspect ratio button selection."""
        self._selected_ratio = value
        for i, btn in enumerate(self._ratio_buttons):
            btn.setChecked(self._ratio_values[i] == value)

    def _on_quality_selected(self, value: str):
        """Handle quality button selection."""
        self._selected_quality = value
        for i, btn in enumerate(self._quality_buttons):
            btn.setChecked(self._quality_values[i] == value)

    # ── Pipeline Step Management ──

    def set_pipeline_step(self, step_index: int):
        """Mark steps up to step_index as completed (0-based)."""
        if step_index < self._pipeline_active:
            return  # Don't go backwards
        self._pipeline_active = step_index + 1
        for i, (circle, label) in enumerate(zip(self._pipeline_circles, self._pipeline_labels)):
            if i <= step_index:
                circle.setText("✓")
                circle.setProperty("active", True)
                label.setProperty("active", True)
            else:
                circle.setText(str(i + 1))
                circle.setProperty("active", False)
                label.setProperty("active", False)
            # Force QSS re-evaluation
            circle.style().unpolish(circle)
            circle.style().polish(circle)
            label.style().unpolish(label)
            label.style().polish(label)

    def reset_pipeline(self):
        """Reset all pipeline steps to inactive."""
        self._pipeline_active = 0
        for i, (circle, label) in enumerate(zip(self._pipeline_circles, self._pipeline_labels)):
            circle.setText(str(i + 1))
            circle.setProperty("active", False)
            label.setProperty("active", False)
            circle.style().unpolish(circle)
            circle.style().polish(circle)
            label.style().unpolish(label)
            label.style().polish(label)

    def _connect_pipeline_signals(self):
        """Connect config panel signals to auto-advance pipeline."""
        # Step 0: Config — any model change
        self._model_combo.currentIndexChanged.connect(lambda: self.set_pipeline_step(0))
        # Step 1: Prompt — text changes
        self._prompt_input.textChanged.connect(lambda: self._check_prompt_step())
        # Step 2: Reference — ref images picked
        self.ref_images_picked.connect(lambda *a: self.set_pipeline_step(2))
        # Step 3: Output — output folder set
        self._output_path.textChanged.connect(lambda t: self.set_pipeline_step(3) if t else None)
        # Step 4: Run — add to queue
        self.add_to_queue.connect(lambda _: self.set_pipeline_step(4))

    def _check_prompt_step(self):
        """Mark prompt step if there's text."""
        if self._prompt_input.toPlainText().strip():
            self.set_pipeline_step(1)
