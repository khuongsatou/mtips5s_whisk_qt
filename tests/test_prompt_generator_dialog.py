"""Tests for app.widgets.prompt_generator_dialog module."""
import json
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QCoreApplication


# ── Helper functions (file I/O) ─────────────────────────────────


class TestLoadSavedPrompts:
    """Tests for _load_saved_prompts()."""

    def test_returns_empty_when_no_file(self, tmp_path):
        fake_path = str(tmp_path / "nonexistent.json")
        with patch("app.widgets.prompt_generator_dialog.SAVED_PROMPTS_PATH", fake_path):
            from app.widgets.prompt_generator_dialog import _load_saved_prompts
            result = _load_saved_prompts()
        assert result == []

    def test_loads_existing_file(self, tmp_path):
        fake_path = str(tmp_path / "prompts.json")
        data = [{"template": "T1", "idea": "I1", "created_at": "2026-01-01"}]
        with open(fake_path, "w") as f:
            json.dump(data, f)
        with patch("app.widgets.prompt_generator_dialog.SAVED_PROMPTS_PATH", fake_path):
            from app.widgets.prompt_generator_dialog import _load_saved_prompts
            result = _load_saved_prompts()
        assert len(result) == 1
        assert result[0]["template"] == "T1"

    def test_returns_empty_on_corrupt_json(self, tmp_path):
        fake_path = str(tmp_path / "corrupt.json")
        with open(fake_path, "w") as f:
            f.write("{{{bad")
        with patch("app.widgets.prompt_generator_dialog.SAVED_PROMPTS_PATH", fake_path):
            from app.widgets.prompt_generator_dialog import _load_saved_prompts
            result = _load_saved_prompts()
        assert result == []

    def test_returns_empty_when_json_is_dict(self, tmp_path):
        fake_path = str(tmp_path / "dict.json")
        with open(fake_path, "w") as f:
            json.dump({"not": "a list"}, f)
        with patch("app.widgets.prompt_generator_dialog.SAVED_PROMPTS_PATH", fake_path):
            from app.widgets.prompt_generator_dialog import _load_saved_prompts
            result = _load_saved_prompts()
        assert result == []


class TestSavePrompts:
    """Tests for _save_prompts()."""

    def test_saves_to_file(self, tmp_path):
        fake_path = str(tmp_path / "prompts.json")
        data = [{"template": "T", "idea": "I"}]
        with patch("app.widgets.prompt_generator_dialog.SAVED_PROMPTS_PATH", fake_path):
            from app.widgets.prompt_generator_dialog import _save_prompts
            _save_prompts(data)
        with open(fake_path, "r") as f:
            loaded = json.load(f)
        assert loaded[0]["template"] == "T"


# ── PromptGeneratorDialog ───────────────────────────────────────


class TestPromptGeneratorDialog:
    """Tests for PromptGeneratorDialog class."""

    @pytest.fixture
    def translator(self):
        t = MagicMock()
        t.t = MagicMock(side_effect=lambda k: k)
        return t

    @pytest.fixture
    def dialog(self, qapp, translator, tmp_path):
        fake_path = str(tmp_path / "prompts.json")
        with open(fake_path, "w") as f:
            json.dump([], f)
        with patch("app.widgets.prompt_generator_dialog.SAVED_PROMPTS_PATH", fake_path):
            from app.widgets.prompt_generator_dialog import PromptGeneratorDialog
            d = PromptGeneratorDialog(translator)
            d._save_path = fake_path
            yield d
            d.close()

    def test_init(self, dialog):
        assert dialog.windowTitle() == "prompt_gen.title"

    def test_template_has_default(self, dialog):
        text = dialog._template_input.toPlainText()
        assert len(text) > 0

    def test_get_full_prompt_both(self, dialog):
        dialog._template_input.setPlainText("Template")
        dialog._idea_input.setPlainText("Idea")
        result = dialog._get_full_prompt()
        assert "Template" in result
        assert "Idea" in result

    def test_get_full_prompt_template_only(self, dialog):
        dialog._template_input.setPlainText("Template")
        dialog._idea_input.clear()
        result = dialog._get_full_prompt()
        assert result == "Template"

    def test_get_full_prompt_idea_only(self, dialog):
        dialog._template_input.clear()
        dialog._idea_input.setPlainText("Idea")
        result = dialog._get_full_prompt()
        assert result == "Idea"

    def test_get_full_prompt_empty(self, dialog):
        dialog._template_input.clear()
        dialog._idea_input.clear()
        result = dialog._get_full_prompt()
        assert result == ""

    def test_on_save_adds_entry(self, dialog, tmp_path):
        fake_path = str(tmp_path / "prompts_save.json")
        with patch("app.widgets.prompt_generator_dialog.SAVED_PROMPTS_PATH", fake_path):
            dialog._template_input.setPlainText("My Template")
            dialog._idea_input.setPlainText("My Idea")
            dialog._on_save()
            assert len(dialog._prompts) == 1
            assert dialog._prompts[0]["template"] == "My Template"
            assert dialog._prompts[0]["idea"] == "My Idea"

    def test_on_save_empty_does_nothing(self, dialog):
        dialog._template_input.clear()
        dialog._idea_input.clear()
        initial_count = len(dialog._prompts)
        dialog._on_save()
        assert len(dialog._prompts) == initial_count

    def test_on_delete_selected_no_selection(self, dialog, tmp_path):
        fake_path = str(tmp_path / "prompts_del.json")
        with patch("app.widgets.prompt_generator_dialog.SAVED_PROMPTS_PATH", fake_path):
            dialog._prompts = [{"template": "T", "idea": "I", "created_at": "now"}]
            dialog._refresh_table()
            # No selection
            dialog._table.clearSelection()
            dialog._on_delete_selected()
            assert len(dialog._prompts) == 1

    def test_refresh_table(self, dialog):
        dialog._prompts = [
            {"template": "T1", "idea": "I1", "created_at": "2026-01-01"},
            {"template": "T2", "idea": "I2", "created_at": "2026-01-02"},
        ]
        dialog._refresh_table()
        assert dialog._table.rowCount() == 2
        assert dialog._table.item(0, 0).text() == "T1"
        assert dialog._table.item(1, 1).text() == "I2"

    def test_on_cell_edited(self, dialog, tmp_path):
        fake_path = str(tmp_path / "prompts_edit.json")
        with patch("app.widgets.prompt_generator_dialog.SAVED_PROMPTS_PATH", fake_path):
            dialog._prompts = [{"template": "T", "idea": "I", "created_at": "now"}]
            dialog._refresh_table()
            # Simulate edit
            from PySide6.QtWidgets import QTableWidgetItem
            dialog._table.setItem(0, 0, QTableWidgetItem("NewT"))
            dialog._on_cell_edited(0, 0)
            assert dialog._prompts[0]["template"] == "NewT"

    def test_on_cell_edited_invalid_row(self, dialog):
        dialog._prompts = []
        dialog._on_cell_edited(-1, 0)  # Should not crash
        dialog._on_cell_edited(99, 0)  # Should not crash
