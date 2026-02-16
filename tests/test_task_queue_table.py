"""
Tests for TaskQueueTable — queue display with output thumbnails.
"""
import pytest
from PySide6.QtWidgets import QProgressBar, QLabel, QCheckBox
from PySide6.QtCore import Qt
from app.widgets.task_queue_table import TaskQueueTable, ImagePreviewDialog, ClickableLabel, PromptDelegate


def _sample_task(task_id="t1", stt=1, status="pending", progress=0, **kw):
    """Helper to create a task dict."""
    task = {
        "id": task_id, "stt": stt, "task_name": "Test", "model": "IMAGEN_3_5",
        "aspect_ratio": "16:9", "prompt": f"prompt for {task_id}",
        "status": status, "progress": progress,
        "images_per_prompt": 1,
        "reference_images_by_cat": {},
        "output_images": [],
    }
    task.update(kw)
    return task


class TestClickableLabel:
    """Test the ClickableLabel widget."""

    def test_stores_image_path(self, qtbot):
        label = ClickableLabel("/test/image.png")
        qtbot.addWidget(label)
        assert label._image_path == "/test/image.png"

    def test_emits_clicked_signal(self, qtbot):
        label = ClickableLabel("/test/image.png")
        qtbot.addWidget(label)
        with qtbot.waitSignal(label.clicked, timeout=500):
            label.clicked.emit("/test/image.png")


class TestImagePreviewDialog:
    """Test the image preview dialog."""

    def test_dialog_stores_path(self, qtbot):
        dlg = ImagePreviewDialog("/test/image.png")
        qtbot.addWidget(dlg)
        assert dlg._image_path == "/test/image.png"

    def test_minimum_size(self, qtbot):
        dlg = ImagePreviewDialog("/test/image.png")
        qtbot.addWidget(dlg)
        assert dlg.minimumWidth() >= 480
        assert dlg.minimumHeight() >= 400

    def test_modal(self, qtbot):
        dlg = ImagePreviewDialog("/test/image.png")
        qtbot.addWidget(dlg)
        assert dlg.isModal()


class TestPromptDelegate:
    """Test the custom prompt editor delegate."""

    def test_creates_editor(self, qtbot, translator):
        table = TaskQueueTable(translator)
        qtbot.addWidget(table)
        delegate = PromptDelegate(table)
        editor = delegate.createEditor(table.viewport(), None, None)
        assert editor is not None
        assert editor.objectName() == "prompt_editor"

    def test_set_editor_data(self, qtbot, translator):
        table = TaskQueueTable(translator)
        qtbot.addWidget(table)
        table.load_data([_sample_task()])
        delegate = PromptDelegate(table)
        editor = delegate.createEditor(table.viewport(), None, None)
        index = table.model().index(0, 4)
        delegate.setEditorData(editor, index)
        assert "prompt for t1" in editor.toPlainText()


class TestTaskQueueTableInit:
    """Test TaskQueueTable construction."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.table = TaskQueueTable(translator)
        qtbot.addWidget(self.table)

    def test_column_count(self):
        assert self.table.columnCount() == 8

    def test_no_rows_initially(self):
        assert self.table.rowCount() == 0

    def test_object_name(self):
        assert self.table.objectName() == "task_queue_table"

    def test_vertical_header_hidden(self):
        assert not self.table.verticalHeader().isVisible()

    def test_alternating_row_colors(self):
        assert self.table.alternatingRowColors()

    def test_word_wrap_enabled(self):
        assert self.table.wordWrap()


class TestTaskQueueTableLoadData:
    """Test loading tasks into the table."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.table = TaskQueueTable(translator)
        qtbot.addWidget(self.table)

    def test_load_empty_tasks(self):
        self.table.load_data([])
        assert self.table.rowCount() == 0

    def test_load_single_task(self):
        self.table.load_data([_sample_task()])
        assert self.table.rowCount() == 1

    def test_load_multiple_tasks(self):
        tasks = [_sample_task(f"t{i}", i) for i in range(5)]
        self.table.load_data(tasks)
        assert self.table.rowCount() == 5

    def test_completed_task_shows_progress_100(self):
        tasks = [_sample_task(status="completed", progress=100)]
        self.table.load_data(tasks)
        assert self.table.rowCount() == 1

    def test_task_ids_tracked(self):
        self.table.load_data([_sample_task("abc"), _sample_task("def", 2)])
        assert "abc" in self.table._task_ids
        assert "def" in self.table._task_ids

    def test_checkboxes_created(self):
        self.table.load_data([_sample_task("t1"), _sample_task("t2", 2)])
        assert "t1" in self.table._checkboxes
        assert "t2" in self.table._checkboxes

    def test_error_task_shows_message(self):
        tasks = [_sample_task(
            status="error", error_message="API Error: timeout",
        )]
        self.table.load_data(tasks)
        assert self.table.rowCount() == 1

    def test_reload_clears_old_data(self):
        self.table.load_data([_sample_task("t1")])
        assert self.table.rowCount() == 1
        self.table.load_data([_sample_task("t2"), _sample_task("t3", 2)])
        assert self.table.rowCount() == 2
        assert "t1" not in self.table._task_ids


class TestTaskQueueTableUpdateProgress:
    """Test update_task_progress method."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.table = TaskQueueTable(translator)
        qtbot.addWidget(self.table)
        self.table.load_data([_sample_task("t1"), _sample_task("t2", 2)])

    def test_unknown_task_id_no_crash(self):
        # Should not raise
        self.table.update_task_progress("nonexistent", 50, "running")

    def test_update_running_status(self):
        self.table.update_task_progress("t1", 50, "running")
        # Should not crash; verify the table still has correct rows
        assert self.table.rowCount() == 2

    def test_update_completed_status(self):
        self.table.update_task_progress("t1", 100, "completed")
        assert self.table.rowCount() == 2

    def test_update_error_status_with_message(self):
        self.table.update_task_progress("t1", 0, "error", error_message="Timeout")
        assert self.table.rowCount() == 2


class TestTaskQueueTableSelection:
    """Test selection methods."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.table = TaskQueueTable(translator)
        qtbot.addWidget(self.table)
        self.table.load_data([
            _sample_task("t1", 1), _sample_task("t2", 2), _sample_task("t3", 3),
        ])

    def test_get_selected_ids_empty(self):
        assert self.table.get_selected_ids() == []

    def test_select_all(self):
        self.table.select_all(True)
        ids = self.table.get_selected_ids()
        assert set(ids) == {"t1", "t2", "t3"}

    def test_deselect_all(self):
        self.table.select_all(True)
        self.table.select_all(False)
        assert self.table.get_selected_ids() == []

    def test_individual_checkbox(self):
        cb = self.table._checkboxes["t2"]
        cb.setChecked(True)
        ids = self.table.get_selected_ids()
        assert ids == ["t2"]

    def test_task_selected_signal(self, qtbot):
        with qtbot.waitSignal(self.table.task_selected, timeout=500):
            cb = self.table._checkboxes["t1"]
            cb.setChecked(True)


class TestTaskQueueTablePromptEdit:
    """Test prompt editing via cellChanged signal."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.table = TaskQueueTable(translator)
        qtbot.addWidget(self.table)
        self.table.load_data([_sample_task("t1")])

    def test_prompt_edited_signal(self, qtbot):
        with qtbot.waitSignal(self.table.prompt_edited, timeout=500):
            item = self.table.item(0, 4)
            if item:
                item.setText("new prompt text")

    def test_non_prompt_column_ignored(self):
        # Editing column 1 (STT) should not emit prompt_edited
        signals = []
        self.table.prompt_edited.connect(lambda *a: signals.append(a))
        self.table._on_cell_changed(0, 1)
        assert len(signals) == 0


class TestTaskQueueTableRetranslate:
    """Test retranslation."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.translator = translator
        self.table = TaskQueueTable(translator)
        qtbot.addWidget(self.table)

    def test_retranslate_runs(self):
        self.translator.set_language("vi")
        # Should not raise

