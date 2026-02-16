"""
Tests for ItemsPage and ItemDialog — items CRUD page.

Uses a MagicMock api since MockApi doesn't implement get_items()/create_item().
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QDialog
from app.pages.items_page import ItemsPage, ItemDialog


@pytest.fixture
def page_api():
    """Mock API that supports get_items / create_item / etc. for ItemsPage."""
    api = MagicMock()
    api.get_items.return_value = MagicMock(
        success=True,
        data=[
            {"id": "1", "name": "Apple", "description": "Fruit", "status": "pending",
             "created_at": "2026-01-01T00:00:00"},
            {"id": "2", "name": "Banana", "description": "Yellow", "status": "completed",
             "created_at": "2026-01-02T00:00:00"},
        ]
    )
    api.create_item.return_value = MagicMock(success=True)
    api.get_item.return_value = MagicMock(success=True, data={
        "id": "1", "name": "Apple", "description": "Fruit", "status": "pending"
    })
    api.update_item.return_value = MagicMock(success=True)
    api.delete_item.return_value = MagicMock(success=True)
    return api


class TestItemDialogInit:
    """Test item dialog construction."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.translator = translator

    def test_create_mode(self, qtbot):
        dlg = ItemDialog(self.translator)
        qtbot.addWidget(dlg)
        assert dlg.minimumWidth() >= 420

    def test_edit_mode(self, qtbot):
        data = {"name": "Test", "description": "Desc", "status": "completed"}
        dlg = ItemDialog(self.translator, item_data=data)
        qtbot.addWidget(dlg)
        assert dlg._name_input.text() == "Test"
        assert dlg._desc_input.toPlainText() == "Desc"

    def test_get_data(self, qtbot):
        dlg = ItemDialog(self.translator)
        qtbot.addWidget(dlg)
        dlg._name_input.setText("New Item")
        dlg._desc_input.setPlainText("Some desc")
        data = dlg.get_data()
        assert data["name"] == "New Item"
        assert data["description"] == "Some desc"
        assert data["status"] == "pending"

    def test_edit_mode_status_selection(self, qtbot):
        data = {"name": "X", "description": "Y", "status": "in_progress"}
        dlg = ItemDialog(self.translator, item_data=data)
        qtbot.addWidget(dlg)
        assert dlg._status_combo.currentData() == "in_progress"


class TestItemsPageInit:
    """Test items page construction."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, page_api):
        self.page = ItemsPage(translator, page_api)
        qtbot.addWidget(self.page)

    def test_has_title(self):
        assert self.page._title is not None

    def test_has_search_input(self):
        assert self.page._search_input is not None

    def test_has_add_button(self):
        assert self.page._add_btn is not None

    def test_has_data_table(self):
        assert self.page._table is not None


class TestItemsPageSearch:
    """Test search filtering."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, page_api):
        self.page = ItemsPage(translator, page_api)
        qtbot.addWidget(self.page)

    def test_search_filters_by_name(self):
        self.page._on_search("Apple")
        assert self.page._table.rowCount() == 1

    def test_search_filters_by_description(self):
        self.page._on_search("Yellow")
        assert self.page._table.rowCount() == 1

    def test_empty_search_shows_all(self):
        self.page._on_search("Apple")
        self.page._on_search("")
        assert self.page._table.rowCount() == 2

    def test_search_no_match(self):
        self.page._on_search("zzzzz")
        assert self.page._table.rowCount() == 0


class TestItemsPageRetranslate:
    """Test retranslation."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, page_api):
        self.translator = translator
        self.page = ItemsPage(translator, page_api)
        qtbot.addWidget(self.page)

    def test_retranslate_updates_title(self):
        self.translator.set_language("vi")
        assert self.page._title.text()  # not empty
