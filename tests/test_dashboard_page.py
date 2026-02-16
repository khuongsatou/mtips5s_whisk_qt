"""
Tests for DashboardPage — welcome message and stat cards.

Uses a MagicMock api since MockApi doesn't implement get_items().
"""
import pytest
from unittest.mock import MagicMock
from app.pages.dashboard_page import DashboardPage


@pytest.fixture
def page_api():
    """Mock API that supports get_items for DashboardPage."""
    api = MagicMock()
    api.get_items.return_value = MagicMock(
        success=True,
        data=[
            {"id": "1", "name": "A", "status": "completed"},
            {"id": "2", "name": "B", "status": "pending"},
            {"id": "3", "name": "C", "status": "in_progress"},
        ]
    )
    return api


class TestDashboardPageInit:
    """Test dashboard construction and initial state."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, page_api):
        self.page = DashboardPage(translator, page_api)
        qtbot.addWidget(self.page)

    def test_has_welcome_title(self):
        assert self.page._welcome_title is not None
        assert self.page._welcome_title.text()

    def test_has_welcome_desc(self):
        assert self.page._welcome_desc is not None

    def test_has_four_stat_cards(self):
        assert self.page._card_total is not None
        assert self.page._card_completed is not None
        assert self.page._card_progress is not None
        assert self.page._card_pending is not None

    def test_stat_cards_have_value_labels(self):
        assert self.page._card_total["value_label"] is not None
        assert self.page._card_completed["value_label"] is not None

    def test_has_recent_title(self):
        assert self.page._recent_title is not None


class TestDashboardPageRefresh:
    """Test data refresh updates cards."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, page_api):
        self.api = page_api
        self.page = DashboardPage(translator, page_api)
        qtbot.addWidget(self.page)

    def test_refresh_counts_total(self):
        self.page.refresh_data()
        assert self.page._card_total["value_label"].text() == "3"

    def test_refresh_counts_completed(self):
        self.page.refresh_data()
        assert self.page._card_completed["value_label"].text() == "1"

    def test_refresh_counts_pending(self):
        self.page.refresh_data()
        assert self.page._card_pending["value_label"].text() == "1"

    def test_refresh_counts_in_progress(self):
        self.page.refresh_data()
        assert self.page._card_progress["value_label"].text() == "1"

    def test_refresh_with_empty_data(self):
        self.api.get_items.return_value = MagicMock(success=True, data=[])
        self.page.refresh_data()
        assert self.page._card_total["value_label"].text() == "0"


class TestDashboardPageRetranslate:
    """Test retranslation."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, page_api):
        self.translator = translator
        self.page = DashboardPage(translator, page_api)
        qtbot.addWidget(self.page)

    def test_retranslate_updates_texts(self):
        self.translator.set_language("vi")
        assert self.page._welcome_title.text()
