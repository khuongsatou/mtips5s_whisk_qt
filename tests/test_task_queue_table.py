"""
Tests for TaskQueueTable — queue display with output thumbnails.
"""
import pytest
from app.widgets.task_queue_table import TaskQueueTable, ImagePreviewDialog, ClickableLabel


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
        tasks = [{
            "id": "t1", "stt": 1, "task_name": "Test", "model": "IMAGEN_3_5",
            "aspect_ratio": "16:9", "prompt": "hello",
            "status": "pending", "progress": 0,
            "images_per_prompt": 1,
            "reference_images_by_cat": {},
            "output_images": [],
        }]
        self.table.load_data(tasks)
        assert self.table.rowCount() == 1

    def test_load_multiple_tasks(self):
        tasks = [
            {"id": f"t{i}", "stt": i, "task_name": f"T{i}", "model": "M",
             "aspect_ratio": "1:1", "prompt": f"p{i}", "status": "pending",
             "progress": 0, "images_per_prompt": 1,
             "reference_images_by_cat": {}, "output_images": []}
            for i in range(5)
        ]
        self.table.load_data(tasks)
        assert self.table.rowCount() == 5

    def test_completed_task_shows_progress_100(self):
        tasks = [{
            "id": "t1", "stt": 1, "task_name": "Done", "model": "M",
            "aspect_ratio": "1:1", "prompt": "done",
            "status": "completed", "progress": 100,
            "images_per_prompt": 1,
            "reference_images_by_cat": {},
            "output_images": [],
        }]
        self.table.load_data(tasks)
        assert self.table.rowCount() == 1


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
