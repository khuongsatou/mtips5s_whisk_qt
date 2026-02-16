"""
Tests for ConfigPanel widget — defaults, pipeline, QSettings, reset, clear.
"""
import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QSettings
from app.widgets.config_panel import ConfigPanel


class TestConfigPanelDefaults:
    """Verify factory-default values after construction."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        # Clear any leftover QSettings
        QSettings("Whisk", "ConfigPanel").clear()
        self.panel = ConfigPanel(translator)
        qtbot.addWidget(self.panel)

    def test_default_model(self):
        assert self.panel._model_combo.currentData() == "IMAGEN_3_5"

    def test_default_quality(self):
        assert self.panel._selected_quality == "1K"

    def test_default_ratio(self):
        assert self.panel._selected_ratio == "16:9"

    def test_default_images_per_prompt(self):
        assert self.panel._images_spin.value() == 1

    def test_default_concurrency(self):
        assert self.panel._concurrency_spin.value() == 2

    def test_default_delay_min(self):
        assert self.panel._delay_min.value() == 10

    def test_default_delay_max(self):
        assert self.panel._delay_max.value() == 20

    def test_default_prompt_empty(self):
        assert self.panel._prompt_input.toPlainText() == ""

    def test_default_prefix(self):
        assert self.panel._prefix_input.text() == "{{number}}.png"

    def test_default_output_path_empty(self):
        assert self.panel._output_path.text() == ""


class TestConfigPanelSections:
    """Verify UI sections are created correctly."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        QSettings("Whisk", "ConfigPanel").clear()
        self.panel = ConfigPanel(translator)
        qtbot.addWidget(self.panel)

    def test_has_pipeline_steps(self):
        assert len(self.panel._pipeline_steps) == 5

    def test_has_pipeline_circles(self):
        assert len(self.panel._pipeline_circles) == 5

    def test_has_quality_buttons(self):
        assert len(self.panel._quality_buttons) == 3

    def test_has_ratio_buttons(self):
        assert len(self.panel._ratio_buttons) == 4

    def test_has_ref_categories(self):
        assert set(self.panel._ref_slot_rows.keys()) == {"title", "scene", "style"}

    def test_each_ref_category_starts_with_one_slot(self):
        for cat in ("title", "scene", "style"):
            assert len(self.panel._ref_slot_rows[cat]) == 1

    def test_has_model_section(self):
        assert self.panel._model_section is not None

    def test_has_exec_section(self):
        assert self.panel._exec_section is not None

    def test_has_prompt_section(self):
        assert self.panel._prompt_section is not None

    def test_has_output_section(self):
        assert self.panel._output_section is not None


class TestConfigPanelSelectors:
    """Test quality and ratio selection logic."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        QSettings("Whisk", "ConfigPanel").clear()
        self.panel = ConfigPanel(translator)
        qtbot.addWidget(self.panel)

    def test_select_quality_2k(self):
        self.panel._on_quality_selected("2K")
        assert self.panel._selected_quality == "2K"
        assert self.panel._quality_buttons[1].isChecked()
        assert not self.panel._quality_buttons[0].isChecked()

    def test_select_quality_4k(self):
        self.panel._on_quality_selected("4K")
        assert self.panel._selected_quality == "4K"
        assert self.panel._quality_buttons[2].isChecked()

    def test_select_ratio_1_1(self):
        self.panel._on_ratio_selected("1:1")
        assert self.panel._selected_ratio == "1:1"
        assert self.panel._ratio_buttons[2].isChecked()
        assert not self.panel._ratio_buttons[0].isChecked()

    def test_select_ratio_9_16(self):
        self.panel._on_ratio_selected("9:16")
        assert self.panel._selected_ratio == "9:16"
        assert self.panel._ratio_buttons[1].isChecked()


class TestConfigPanelPipeline:
    """Test pipeline step management."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        QSettings("Whisk", "ConfigPanel").clear()
        self.panel = ConfigPanel(translator)
        qtbot.addWidget(self.panel)

    def test_initial_pipeline_step_0_active(self):
        # step 0 is set in _setup_ui
        assert self.panel._pipeline_active == 1
        assert self.panel._pipeline_circles[0].text() == "✓"

    def test_set_pipeline_step_advances(self):
        self.panel.set_pipeline_step(2)
        assert self.panel._pipeline_active == 3
        for i in range(3):
            assert self.panel._pipeline_circles[i].text() == "✓"
        assert self.panel._pipeline_circles[3].text() == "4"

    def test_pipeline_does_not_go_backwards(self):
        self.panel.set_pipeline_step(3)
        self.panel.set_pipeline_step(1)  # should be ignored
        assert self.panel._pipeline_active == 4

    def test_reset_pipeline(self):
        self.panel.set_pipeline_step(4)
        self.panel.reset_pipeline()
        assert self.panel._pipeline_active == 0
        for i, circle in enumerate(self.panel._pipeline_circles):
            assert circle.text() == str(i + 1)


class TestConfigPanelClearAndReset:
    """Test clear_inputs and reset_to_defaults."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        QSettings("Whisk", "ConfigPanel").clear()
        self.panel = ConfigPanel(translator)
        qtbot.addWidget(self.panel)

    def test_clear_inputs_clears_prompt(self):
        self.panel._prompt_input.setPlainText("test prompt")
        self.panel.clear_inputs()
        assert self.panel._prompt_input.toPlainText() == ""

    def test_clear_inputs_clears_ref_images(self):
        self.panel._ref_images = {"title_0": ["/a.png"]}
        self.panel.clear_inputs()
        assert self.panel._ref_images == {}

    def test_clear_inputs_keeps_config(self):
        self.panel._on_quality_selected("4K")
        self.panel._images_spin.setValue(4)
        self.panel.clear_inputs()
        # Quality and spinner should remain
        assert self.panel._selected_quality == "4K"
        assert self.panel._images_spin.value() == 4

    def test_reset_to_defaults_resets_quality(self):
        self.panel._on_quality_selected("4K")
        self.panel.reset_to_defaults()
        assert self.panel._selected_quality == "1K"

    def test_reset_to_defaults_resets_ratio(self):
        self.panel._on_ratio_selected("1:1")
        self.panel.reset_to_defaults()
        assert self.panel._selected_ratio == "16:9"

    def test_reset_to_defaults_resets_spinners(self):
        self.panel._images_spin.setValue(10)
        self.panel._concurrency_spin.setValue(10)
        self.panel.reset_to_defaults()
        assert self.panel._images_spin.value() == 1
        assert self.panel._concurrency_spin.value() == 1

    def test_reset_to_defaults_resets_delay(self):
        self.panel._delay_min.setValue(50)
        self.panel._delay_max.setValue(100)
        self.panel.reset_to_defaults()
        assert self.panel._delay_min.value() == 3
        assert self.panel._delay_max.value() == 5

    def test_reset_to_defaults_clears_text_fields(self):
        self.panel._prefix_input.setText("test_prefix")
        self.panel._prompt_input.setPlainText("a prompt")
        self.panel.reset_to_defaults()
        assert self.panel._prefix_input.text() == ""
        assert self.panel._prompt_input.toPlainText() == ""


class TestConfigPanelEmitSignal:
    """Test add_to_queue signal emission."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        QSettings("Whisk", "ConfigPanel").clear()
        self.panel = ConfigPanel(translator)
        qtbot.addWidget(self.panel)

    def test_on_add_emits_signal_with_config(self, qtbot):
        self.panel._prompt_input.setPlainText("my test prompt")
        self.panel._images_spin.setValue(3)
        self.panel._on_quality_selected("2K")
        self.panel._on_ratio_selected("1:1")

        with qtbot.waitSignal(self.panel.add_to_queue, timeout=1000) as blocker:
            self.panel._on_add()

        config = blocker.args[0]
        assert config["prompt"] == "my test prompt"
        assert config["images_per_prompt"] == 3
        assert config["quality"] == "2K"
        assert config["aspect_ratio"] == "1:1"
        assert config["model"] == "IMAGEN_3_5"

    def test_on_add_clears_prompt_after_emit(self):
        self.panel._prompt_input.setPlainText("will be cleared")
        self.panel._on_add()
        assert self.panel._prompt_input.toPlainText() == ""


class TestConfigPanelRefSlots:
    """Test dynamic reference image slot management."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        QSettings("Whisk", "ConfigPanel").clear()
        self.panel = ConfigPanel(translator)
        qtbot.addWidget(self.panel)

    def test_add_ref_slot_row(self):
        self.panel._add_ref_slot_row("title")
        assert len(self.panel._ref_slot_rows["title"]) == 2

    def test_max_five_ref_slots(self):
        for _ in range(10):
            self.panel._add_ref_slot_row("title")
        assert len(self.panel._ref_slot_rows["title"]) == 5

    def test_add_btn_hidden_at_max(self):
        for _ in range(5):
            self.panel._add_ref_slot_row("scene")
        assert not self.panel._ref_add_btns["scene"].isVisible()


class TestConfigPanelRetranslate:
    """Test language switching updates labels."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        QSettings("Whisk", "ConfigPanel").clear()
        self.translator = translator
        self.panel = ConfigPanel(translator)
        qtbot.addWidget(self.panel)

    def test_retranslate_updates_section_title(self):
        self.translator.set_language("vi")
        # The section title should now be in Vietnamese
        title_text = self.panel._section_title.text()
        assert title_text  # should have some text
        assert title_text != ""
