"""
Whisk Desktop — Config Panel Settings & Event Handlers.

Mixin class providing settings persistence, event handlers, ref mode logic,
pipeline management, retranslation, and other config panel behaviors.
"""
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog,
)
from PySide6.QtCore import Qt, QSettings


class SettingsHandlersMixin:
    """Mixin providing settings, event handlers, and pipeline management."""

    # --- Reference mode ---

    def _set_ref_mode(self, mode: str):
        """Switch ref mode and update button styles."""
        self._current_ref_mode = mode
        self._ref_mode_btn_multi.setChecked(mode == "multiple")
        self._ref_mode_btn_single.setChecked(mode == "single")
        self._apply_ref_mode_styles()

        is_single = mode == "single"
        for cat in ("title", "scene", "style"):
            self._ref_getid_rows[cat].setVisible(is_single)
            if not is_single:
                self._preloaded_media_inputs[cat] = []
                self._ref_id_statuses[cat].setText("")

    _REF_MODE_ACTIVE = (
        "QPushButton { background: #3498db; color: white; border: 2px solid #2980b9;"
        " border-radius: 8px; font-weight: bold; font-size: 12px; padding: 4px 8px; }"
    )
    _REF_MODE_INACTIVE = (
        "QPushButton { background: #ecf0f1; color: #7f8c8d; border: 2px solid #bdc3c7;"
        " border-radius: 8px; font-size: 12px; padding: 4px 8px; }"
        " QPushButton:hover { background: #d5dbdb; border-color: #95a5a6; }"
    )

    def _apply_ref_mode_styles(self):
        """Apply active/inactive style to mode toggle buttons."""
        if self._current_ref_mode == "multiple":
            self._ref_mode_btn_multi.setStyleSheet(self._REF_MODE_ACTIVE)
            self._ref_mode_btn_single.setStyleSheet(self._REF_MODE_INACTIVE)
        else:
            self._ref_mode_btn_multi.setStyleSheet(self._REF_MODE_INACTIVE)
            self._ref_mode_btn_single.setStyleSheet(self._REF_MODE_ACTIVE)

    def _on_get_ref_id(self, category: str):
        """Request pre-upload of reference images for a specific category."""
        ref_images = getattr(self, '_ref_images', {})
        cat_images = []
        for idx in range(5):
            cat_images.extend(ref_images.get(f"{category}_{idx}", []))

        if not cat_images:
            self._ref_id_statuses[category].setText("⚠️ No images")
            return

        self._ref_id_statuses[category].setText(self.translator.t("config.ref_id_getting"))
        self._ref_getid_btns[category].setEnabled(False)
        self._preloaded_media_inputs[category] = []
        self.request_upload_ref.emit(category, {category: cat_images})

    def set_preloaded_media_inputs(self, category: str, media_inputs: list):
        """Called by page after pre-upload completes for a specific category."""
        self._preloaded_media_inputs[category] = media_inputs
        self._ref_getid_btns[category].setEnabled(True)
        if media_inputs:
            count = len(media_inputs)
            text = self.translator.t("config.ref_id_ready").replace("{count}", str(count))
            self._ref_id_statuses[category].setText(text)
        else:
            self._ref_id_statuses[category].setText(self.translator.t("config.ref_id_error"))

    def _get_all_preloaded(self) -> list:
        """Flatten per-category preloaded media inputs into a single list."""
        result = []
        for cat in ("title", "scene", "style"):
            result.extend(self._preloaded_media_inputs.get(cat, []))
        return result

    # --- File / folder dialogs ---

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

    # --- Add to queue ---

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

        ref_mode = self._current_ref_mode
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
            "ref_mode": ref_mode,
            "preloaded_media_inputs": self._get_all_preloaded() if ref_mode == "single" else [],
        }
        self.add_to_queue.emit(config)

        # Save settings (keep config values) then clear prompt + refs
        self._save_settings()
        self.clear_inputs()

    # --- Prompt count ---

    def _update_prompt_count(self):
        """Update the prompt count label based on split mode."""
        text = self._prompt_input.toPlainText().strip()
        if not text:
            self._prompt_count_label.setText("")
            return

        mode = self._split_combo.currentData() or "auto"

        if mode == "json":
            count = 1
        elif mode == "paragraph":
            parts = [p.strip() for p in text.split("\n\n") if p.strip()]
            count = len(parts)
        elif mode == "single":
            parts = [ln.strip() for ln in text.split("\n") if ln.strip()]
            count = len(parts)
        else:  # auto
            # Check if it looks like JSON
            s = text.strip()
            if (s.startswith("{") and s.endswith("}")) or \
               (s.startswith("[") and s.endswith("]")):
                count = 1
            else:
                parts = [ln.strip() for ln in text.split("\n") if ln.strip()]
                count = len(parts)

        self._prompt_count_label.setText(f"📝 {count} prompt(s)")

    # --- Selection handlers ---

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
        s.setValue("auto_retry", self._auto_retry_cb.isChecked())

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

        # Auto-retry
        auto_retry = s.value("auto_retry", False, type=bool)
        self._auto_retry_cb.setChecked(auto_retry)

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
            self._ratio_buttons[i].setChecked(val == "16:9")
        # Spinners
        self._images_spin.setValue(1)
        self._concurrency_spin.setValue(1)
        self._delay_min.setValue(3)
        self._delay_max.setValue(5)
        # Split mode
        self._split_combo.setCurrentIndex(0)
        # Auto-retry
        self._auto_retry_cb.setChecked(False)
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

    # --- Retranslation ---

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
        self._auto_retry_cb.setText(self.translator.t('config.auto_retry'))
        self._file_btn.setText(f"📄 {self.translator.t('config.load_file')}")
        self._prompt_label.setText(f"💬 {self.translator.t('config.prompt')}")
        self._prompt_input.setPlaceholderText(self.translator.t("config.prompt_placeholder"))
        self._prefix_label.setText(f"🏷️ {self.translator.t('config.filename_prefix')}")
        self._output_label.setText(f"📂 {self.translator.t('config.output_folder')}")
        self._ref_section.set_title(f"🖼️ {self.translator.t('config.section_ref_images')}")
        self._ref_title_label.setText(f"🎨 {self.translator.t('config.ref_title')}")
        self._ref_scene_label.setText(f"🎬 {self.translator.t('config.ref_scene')}")
        self._ref_style_label.setText(f"✨ {self.translator.t('config.ref_style')}")
        # Update ref mode toggle button texts
        self._ref_mode_btn_multi.setText("📋 " + self.translator.t("config.ref_mode_multiple"))
        self._ref_mode_btn_single.setText("🔗 " + self.translator.t("config.ref_mode_single"))
        for cat in ("title", "scene", "style"):
            self._ref_getid_btns[cat].setText(self.translator.t("config.ref_get_id"))
        self._add_btn.setText(f"➕ {self.translator.t('config.add_to_queue')}")

    # --- Workflow status ---

    def set_workflow_status(self, text: str, error: bool = False):
        """Update the workflow status label below the New Workflow button."""
        self._workflow_status.setText(text)
        self._workflow_status.setStyleSheet(
            "color: #e74c3c; padding: 4px;" if error
            else "color: #27ae60; padding: 4px;"
        )
        self._workflow_status.setVisible(bool(text))
        # Enable "Add to queue" button when workflow is linked
        is_linked = "✅" in text
        self._add_btn.setEnabled(is_linked)

    def set_workflow_btn_enabled(self, enabled: bool):
        """Enable/disable the New Workflow button."""
        self._workflow_btn.setEnabled(enabled)

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

    @property
    def is_auto_retry_enabled(self) -> bool:
        """Whether auto-retry is enabled."""
        return self._auto_retry_cb.isChecked()

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
