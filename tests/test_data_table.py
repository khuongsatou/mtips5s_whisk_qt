"""
Tests for DataTable — reusable table with status badges and action buttons.
"""
import pytest
from app.widgets.data_table import DataTable


SAMPLE_ITEMS = [
    {"id": "1", "name": "Item A", "description": "Desc A", "status": "pending",
     "created_at": "2026-01-01T12:00:00"},
    {"id": "2", "name": "Item B", "description": "Desc B", "status": "completed",
     "created_at": "2026-01-02T12:00:00"},
    {"id": "3", "name": "Item C", "description": "Desc C", "status": "in_progress",
     "created_at": "2026-01-03"},
]


class TestDataTableInit:
    """Test initial table structure."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.table = DataTable(translator)
        qtbot.addWidget(self.table)

    def test_column_count(self):
        assert self.table.columnCount() == 5

    def test_no_rows_initially(self):
        assert self.table.rowCount() == 0

    def test_alternating_row_colors(self):
        assert self.table.alternatingRowColors()

    def test_vertical_header_hidden(self):
        assert not self.table.verticalHeader().isVisible()

    def test_no_grid(self):
        assert not self.table.showGrid()


class TestDataTableLoadData:
    """Test loading data into the table."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.table = DataTable(translator)
        qtbot.addWidget(self.table)

    def test_load_sets_row_count(self):
        self.table.load_data(SAMPLE_ITEMS)
        assert self.table.rowCount() == 3

    def test_load_stores_item_ids(self):
        self.table.load_data(SAMPLE_ITEMS)
        assert self.table._item_ids == ["1", "2", "3"]

    def test_load_name_column(self):
        self.table.load_data(SAMPLE_ITEMS)
        assert self.table.item(0, 0).text() == "Item A"

    def test_load_description_column(self):
        self.table.load_data(SAMPLE_ITEMS)
        assert self.table.item(1, 1).text() == "Desc B"

    def test_load_date_shows_date_only(self):
        self.table.load_data(SAMPLE_ITEMS)
        assert self.table.item(0, 3).text() == "2026-01-01"

    def test_load_date_no_T(self):
        self.table.load_data(SAMPLE_ITEMS)
        assert self.table.item(2, 3).text() == "2026-01-03"

    def test_reload_clears_old_data(self):
        self.table.load_data(SAMPLE_ITEMS)
        self.table.load_data([SAMPLE_ITEMS[0]])
        assert self.table.rowCount() == 1

    def test_load_empty_list(self):
        self.table.load_data([])
        assert self.table.rowCount() == 0

    def test_status_badge_widget_exists(self):
        self.table.load_data(SAMPLE_ITEMS)
        widget = self.table.cellWidget(0, 2)
        assert widget is not None


class TestDataTableSignals:
    """Test edit/delete signal emission."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.table = DataTable(translator)
        self.qtbot = qtbot
        qtbot.addWidget(self.table)
        self.table.load_data(SAMPLE_ITEMS)

    def test_edit_signal_emits_id(self):
        with self.qtbot.waitSignal(self.table.edit_clicked, timeout=500) as blocker:
            actions = self.table.cellWidget(0, 4)
            edit_btn = actions.findChildren(type(actions).findChildren.__self__.__class__)[0] if False else None
            # Click the edit button directly (first QPushButton in actions widget)
            from PySide6.QtWidgets import QPushButton
            btns = actions.findChildren(QPushButton)
            btns[0].click()
        assert blocker.args == ["1"]

    def test_delete_signal_emits_id(self):
        with self.qtbot.waitSignal(self.table.delete_clicked, timeout=500) as blocker:
            from PySide6.QtWidgets import QPushButton
            actions = self.table.cellWidget(1, 4)
            btns = actions.findChildren(QPushButton)
            btns[1].click()
        assert blocker.args == ["2"]


class TestDataTableRetranslate:
    """Test retranslation updates headers."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.translator = translator
        self.table = DataTable(translator)
        qtbot.addWidget(self.table)

    def test_retranslate_runs(self):
        self.translator.set_language("vi")
        self.table.retranslate()
        # Should not raise
