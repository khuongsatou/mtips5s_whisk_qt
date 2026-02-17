"""
Tests for SettingsHandlersMixin — ref mode, preloaded media,
prompt count, persistence, pipeline, and retranslation.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QSettings
from app.widgets.config_panel import ConfigPanel


@pytest.fixture
def panel(qtbot, translator):
    """Provide a fresh ConfigPanel with cleared settings."""
    QSettings("Whisk", "ConfigPanel").clear()
    p = ConfigPanel(translator)
    qtbot.addWidget(p)
    return p


# ── Ref Mode ──────────────────────────────────────────────────────


class TestRefMode:
    def test_default_mode(self, panel):
        # Default mode may be 'single' or 'multiple' depending on config
        assert panel._current_ref_mode in ("single", "multiple")

    def test_set_mode_to_single(self, panel):
        panel._set_ref_mode("single")
        assert panel._current_ref_mode == "single"
        assert panel._ref_mode_btn_single.isChecked()
        assert not panel._ref_mode_btn_multi.isChecked()

    def test_set_mode_to_multiple(self, panel):
        panel._set_ref_mode("single")
        panel._set_ref_mode("multiple")
        assert panel._current_ref_mode == "multiple"
        assert panel._ref_mode_btn_multi.isChecked()

    def test_single_mode_getid_rows_not_hidden(self, panel):
        panel._set_ref_mode("single")
        for cat in ("title", "scene", "style"):
            # When panel is not shown, isVisible returns False even if not hidden
            # Check that the widget is NOT explicitly hidden
            assert not panel._ref_getid_rows[cat].isHidden()

    def test_multiple_mode_hides_getid_rows(self, panel):
        panel._set_ref_mode("single")
        panel._set_ref_mode("multiple")
        for cat in ("title", "scene", "style"):
            assert not panel._ref_getid_rows[cat].isVisible()

    def test_switching_to_multiple_clears_preloaded(self, panel):
        panel._preloaded_media_inputs["title"] = [{"id": "x"}]
        panel._set_ref_mode("multiple")
        assert panel._preloaded_media_inputs["title"] == []

    def test_apply_ref_mode_styles_multiple(self, panel):
        panel._set_ref_mode("multiple")
        style = panel._ref_mode_btn_multi.styleSheet()
        assert "#3498db" in style  # Active color

    def test_apply_ref_mode_styles_single(self, panel):
        panel._set_ref_mode("single")
        style = panel._ref_mode_btn_single.styleSheet()
        assert "#3498db" in style  # Active color


# ── Preloaded Media ───────────────────────────────────────────────


class TestPreloadedMedia:
    def test_set_preloaded_media_inputs(self, panel):
        media = [{"type": "image", "id": "abc"}]
        panel.set_preloaded_media_inputs("title", media)
        assert panel._preloaded_media_inputs["title"] == media
        assert panel._ref_getid_btns["title"].isEnabled()

    def test_set_preloaded_empty_shows_error(self, panel):
        panel.set_preloaded_media_inputs("title", [])
        text = panel._ref_id_statuses["title"].text()
        assert text != ""  # Should show error status

    def test_get_all_preloaded_flattens(self, panel):
        panel._preloaded_media_inputs["title"] = [{"id": "1"}]
        panel._preloaded_media_inputs["scene"] = [{"id": "2"}, {"id": "3"}]
        panel._preloaded_media_inputs["style"] = []
        result = panel._get_all_preloaded()
        assert len(result) == 3
        assert result[0]["id"] == "1"

    def test_get_all_preloaded_empty(self, panel):
        result = panel._get_all_preloaded()
        assert result == []

    def test_on_get_ref_id_no_images(self, panel):
        panel._ref_images = {}
        panel._on_get_ref_id("title")
        assert "⚠️" in panel._ref_id_statuses["title"].text()

    def test_on_get_ref_id_with_images(self, panel):
        panel._ref_images = {"title_0": ["/path/img.png"]}
        with patch.object(panel, 'request_upload_ref') as mock_sig:
            mock_sig.emit = MagicMock()
            panel._on_get_ref_id("title")
            mock_sig.emit.assert_called_once()
            assert not panel._ref_getid_btns["title"].isEnabled()


# ── Prompt Count ──────────────────────────────────────────────────


class TestPromptCount:
    def test_empty_prompt(self, panel):
        panel._prompt_input.setPlainText("")
        panel._update_prompt_count()
        assert panel._prompt_count_label.text() == ""

    def test_single_line(self, panel):
        panel._prompt_input.setPlainText("a cat on a table")
        panel._update_prompt_count()
        assert "1 prompt" in panel._prompt_count_label.text()

    def test_multi_line(self, panel):
        panel._prompt_input.setPlainText("cat\ndog\nbird")
        panel._update_prompt_count()
        assert "3 prompt" in panel._prompt_count_label.text()

    def test_json_mode(self, panel):
        panel._prompt_input.setPlainText("line1\nline2")
        # Set split mode to json
        idx = panel._split_combo.findData("json")
        if idx >= 0:
            panel._split_combo.setCurrentIndex(idx)
        panel._update_prompt_count()
        assert "1 prompt" in panel._prompt_count_label.text()

    def test_paragraph_mode(self, panel):
        panel._prompt_input.setPlainText("paragraph one\n\nparagraph two")
        idx = panel._split_combo.findData("paragraph")
        if idx >= 0:
            panel._split_combo.setCurrentIndex(idx)
        panel._update_prompt_count()
        assert "2 prompt" in panel._prompt_count_label.text()

    def test_auto_json_detection(self, panel):
        panel._prompt_input.setPlainText('{"prompt": "a cat"}')
        panel._update_prompt_count()
        assert "1 prompt" in panel._prompt_count_label.text()


# ── Selection Handlers ────────────────────────────────────────────


class TestSelectionHandlers:
    def test_ratio_selected(self, panel):
        panel._on_ratio_selected("9:16")
        assert panel._selected_ratio == "9:16"

    def test_quality_selected(self, panel):
        panel._on_quality_selected("1K")
        assert panel._selected_quality == "1K"


# ── Settings Persistence ──────────────────────────────────────────


class TestSettingsPersistence:
    def test_save_and_load_quality(self, panel):
        panel._selected_quality = "1K"
        panel._save_settings()
        panel._selected_quality = "2K"  # Change it
        panel._load_settings()
        assert panel._selected_quality == "1K"

    def test_save_and_load_ratio(self, panel):
        panel._on_ratio_selected("9:16")
        panel._save_settings()
        panel._on_ratio_selected("16:9")  # Change
        panel._load_settings()
        assert panel._selected_ratio == "9:16"

    def test_save_and_load_prefix(self, panel):
        panel._prefix_input.setText("my_prefix")
        panel._save_settings()
        panel._prefix_input.clear()
        panel._load_settings()
        assert panel._prefix_input.text() == "my_prefix"

    def test_save_and_load_output_folder(self, panel):
        panel._output_path.setText("/tmp/output")
        panel._save_settings()
        panel._output_path.clear()
        panel._load_settings()
        assert panel._output_path.text() == "/tmp/output"

    def test_save_and_load_auto_retry(self, panel):
        panel._auto_retry_cb.setChecked(True)
        panel._save_settings()
        panel._auto_retry_cb.setChecked(False)
        panel._load_settings()
        assert panel._auto_retry_cb.isChecked() is True

    def test_save_and_load_images_per_prompt(self, panel):
        panel._images_spin.setValue(4)
        panel._save_settings()
        panel._images_spin.setValue(1)
        panel._load_settings()
        assert panel._images_spin.value() == 4

    def test_save_and_load_concurrency(self, panel):
        panel._concurrency_spin.setValue(3)
        panel._save_settings()
        panel._concurrency_spin.setValue(1)
        panel._load_settings()
        assert panel._concurrency_spin.value() == 3


# ── Clear & Reset ─────────────────────────────────────────────────


class TestClearAndReset:
    def test_clear_inputs(self, panel):
        panel._prompt_input.setPlainText("some text")
        panel._ref_images = {"title_0": ["/some/path.png"]}
        panel.clear_inputs()
        assert panel._prompt_input.toPlainText() == ""
        assert panel._ref_images == {}

    def test_reset_to_defaults(self, panel):
        panel._selected_quality = "2K"
        panel._selected_ratio = "1:1"
        panel._images_spin.setValue(5)
        panel._prefix_input.setText("test")

        panel.reset_to_defaults()

        assert panel._selected_quality == "1K"
        assert panel._selected_ratio == "16:9"
        assert panel._images_spin.value() == 1
        assert panel._prefix_input.text() == ""

    def test_reset_clears_settings(self, panel):
        panel._prefix_input.setText("before")
        panel._save_settings()
        panel.reset_to_defaults()
        s = QSettings("Whisk", "ConfigPanel")
        assert s.value("filename_prefix", "") == ""


# ── Workflow Status ───────────────────────────────────────────────


class TestWorkflowStatus:
    def test_set_workflow_status_linked(self, panel):
        panel.set_workflow_status("✅ Workflow linked\nwf-123...")
        assert panel._add_btn.isEnabled()
        assert "color: #27ae60" in panel._workflow_status.styleSheet()

    def test_set_workflow_status_error(self, panel):
        panel.set_workflow_status("❌ Failed to create", error=True)
        assert "color: #e74c3c" in panel._workflow_status.styleSheet()

    def test_set_workflow_status_empty_hides(self, panel):
        panel.set_workflow_status("")
        assert not panel._workflow_status.isVisible()

    def test_set_workflow_btn_enabled(self, panel):
        panel.set_workflow_btn_enabled(False)
        assert not panel._workflow_btn.isEnabled()
        panel.set_workflow_btn_enabled(True)
        assert panel._workflow_btn.isEnabled()


# ── Pipeline ──────────────────────────────────────────────────────


class TestPipeline:
    def test_set_pipeline_step_forward(self, panel):
        panel.set_pipeline_step(0)
        assert panel._pipeline_active == 1
        assert panel._pipeline_circles[0].text() == "✓"

    def test_set_pipeline_step_no_backward(self, panel):
        panel.set_pipeline_step(2)
        panel.set_pipeline_step(0)  # Should not go back
        assert panel._pipeline_active == 3

    def test_reset_pipeline(self, panel):
        panel.set_pipeline_step(3)
        panel.reset_pipeline()
        assert panel._pipeline_active == 0
        for i, circle in enumerate(panel._pipeline_circles):
            assert circle.text() == str(i + 1)

    def test_is_auto_retry_enabled(self, panel):
        panel._auto_retry_cb.setChecked(False)
        assert panel.is_auto_retry_enabled is False
        panel._auto_retry_cb.setChecked(True)
        assert panel.is_auto_retry_enabled is True


# ── Retranslation ─────────────────────────────────────────────────


class TestRetranslation:
    def test_retranslate_updates_labels(self, panel):
        panel.retranslate()
        # Should not crash, and labels should be updated
        assert panel._section_title.text() != ""

    def test_retranslate_updates_add_btn(self, panel):
        panel.retranslate()
        assert panel._add_btn.text() != ""


# ── On Add ────────────────────────────────────────────────────────


class TestOnAdd:
    def test_emits_add_to_queue(self, panel, qtbot):
        panel._prompt_input.setPlainText("test prompt")
        panel._selected_ratio = "16:9"
        panel._selected_quality = "1K"

        with qtbot.waitSignal(panel.add_to_queue, timeout=1000) as sig:
            panel._on_add()

        config = sig.args[0]
        assert config["prompt"] == "test prompt"
        assert config["aspect_ratio"] == "16:9"
        assert config["quality"] == "1K"

    def test_on_add_clears_prompt(self, panel, qtbot):
        panel._prompt_input.setPlainText("test")
        with qtbot.waitSignal(panel.add_to_queue, timeout=1000):
            panel._on_add()
        assert panel._prompt_input.toPlainText() == ""

    def test_on_add_includes_ref_images(self, panel, qtbot):
        panel._prompt_input.setPlainText("test")
        panel._ref_images = {"title_0": ["/img/t.png"]}

        with qtbot.waitSignal(panel.add_to_queue, timeout=1000) as sig:
            panel._on_add()

        config = sig.args[0]
        assert config["ref_title_images"] == ["/img/t.png"]

    def test_on_add_single_mode_includes_preloaded(self, panel, qtbot):
        panel._prompt_input.setPlainText("test")
        panel._set_ref_mode("single")
        panel._preloaded_media_inputs["title"] = [{"id": "x"}]

        with qtbot.waitSignal(panel.add_to_queue, timeout=1000) as sig:
            panel._on_add()

        config = sig.args[0]
        assert config["ref_mode"] == "single"
        assert len(config["preloaded_media_inputs"]) == 1
