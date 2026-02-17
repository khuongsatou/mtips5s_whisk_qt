"""
Tests for DashboardPage — stat cards, completion rate, recent activity, error summary.

Uses a MagicMock api with get_queue() returning task data.
"""
import pytest
from unittest.mock import MagicMock
from app.api.models import ApiResponse
from app.pages.dashboard_page import DashboardPage


def _mock_api(tasks=None):
    """Create mock API with get_queue returning given tasks."""
    api = MagicMock()
    if tasks is None:
        tasks = [
            {"id": "1", "prompt": "sunset", "status": "completed", "completed_at": "2026-02-17 12:00"},
            {"id": "2", "prompt": "mountain", "status": "pending"},
            {"id": "3", "prompt": "ocean", "status": "running"},
            {"id": "4", "prompt": "bad prompt", "status": "error", "error_message": "Timeout"},
        ]
    api.get_queue.return_value = ApiResponse(success=True, data=tasks)
    return api


class TestDashboardInit:
    """Test dashboard construction and initial state."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.api = _mock_api()
        self.page = DashboardPage(translator, self.api)
        qtbot.addWidget(self.page)

    def test_has_welcome_title(self):
        assert self.page._welcome_title is not None
        assert self.page._welcome_title.text()

    def test_has_welcome_desc(self):
        assert self.page._welcome_desc is not None

    def test_has_four_stat_cards(self):
        assert self.page._card_total is not None
        assert self.page._card_completed is not None
        assert self.page._card_pending is not None
        assert self.page._card_errors is not None

    def test_stat_cards_have_labels(self):
        assert self.page._card_total["value_label"] is not None
        assert self.page._card_total["text_label"] is not None

    def test_has_completion_bar(self):
        assert self.page._completion_bar is not None

    def test_has_recent_title(self):
        assert self.page._recent_title is not None

    def test_has_error_title(self):
        assert self.page._error_title is not None

    def test_has_project_title(self):
        assert self.page._project_title is not None

    def test_object_name(self):
        assert self.page.objectName() == "dashboard_page"


class TestDashboardRefresh:
    """Test data refresh updates stat cards."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.api = _mock_api()
        self.page = DashboardPage(translator, self.api)
        qtbot.addWidget(self.page)

    def test_refresh_total(self):
        self.page.refresh_data()
        assert self.page._card_total["value_label"].text() == "4"

    def test_refresh_completed(self):
        self.page.refresh_data()
        assert self.page._card_completed["value_label"].text() == "1"

    def test_refresh_pending(self):
        self.page.refresh_data()
        # pending + running
        assert self.page._card_pending["value_label"].text() == "2"

    def test_refresh_errors(self):
        self.page.refresh_data()
        assert self.page._card_errors["value_label"].text() == "1"

    def test_completion_rate(self):
        self.page.refresh_data()
        assert self.page._completion_bar.value() == 25  # 1/4 = 25%
        assert "25%" in self.page._rate_percent.text()

    def test_completion_rate_all_done(self):
        self.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[
                {"id": "1", "status": "completed"},
                {"id": "2", "status": "completed"},
            ],
        )
        self.page.refresh_data()
        assert self.page._completion_bar.value() == 100

    def test_empty_queue(self):
        self.api.get_queue.return_value = ApiResponse(success=True, data=[])
        self.page.refresh_data()
        assert self.page._card_total["value_label"].text() == "0"
        assert self.page._completion_bar.value() == 0

    def test_api_failure(self):
        self.api.get_queue.return_value = ApiResponse(success=False, message="err")
        self.page.refresh_data()
        # Cards remain at initial "0" values
        assert self.page._card_total["value_label"].text() == "0"


class TestDashboardRecent:
    """Test recent completed tasks list."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.api = _mock_api()
        self.page = DashboardPage(translator, self.api)
        qtbot.addWidget(self.page)

    def test_recent_shows_completed(self):
        self.page.refresh_data()
        count = self.page._recent_container.count()
        assert count >= 1  # At least one completed task

    def test_no_completed_shows_empty_state(self):
        self.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[{"id": "1", "status": "pending"}],
        )
        self.page.refresh_data()
        assert self.page._recent_container.count() == 1  # empty state label


class TestDashboardErrors:
    """Test error summary section."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.api = _mock_api()
        self.page = DashboardPage(translator, self.api)
        qtbot.addWidget(self.page)

    def test_errors_shown(self):
        self.page.refresh_data()
        count = self.page._error_container.count()
        assert count >= 1  # At least one error task

    def test_no_errors_shows_empty_state(self):
        self.api.get_queue.return_value = ApiResponse(
            success=True,
            data=[{"id": "1", "status": "completed"}],
        )
        self.page.refresh_data()
        assert self.page._error_container.count() == 1  # "No errors" label


class TestDashboardRetranslate:
    """Test retranslation updates labels."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.translator = translator
        self.api = _mock_api()
        self.page = DashboardPage(translator, self.api)
        qtbot.addWidget(self.page)

    def test_retranslate_updates_welcome(self):
        self.translator.set_language("vi")
        assert self.page._welcome_title.text()

    def test_retranslate_updates_cards(self):
        self.translator.set_language("vi")
        assert self.page._card_total["text_label"].text()
        assert self.page._card_errors["text_label"].text()

    def test_retranslate_updates_sections(self):
        self.translator.set_language("vi")
        assert self.page._rate_title.text()
        assert self.page._recent_title.text()
        assert self.page._error_title.text()
        assert self.page._project_title.text()


class TestDashboardProjects:
    """Test per-project breakdown."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.api = _mock_api()
        self.page = DashboardPage(translator, self.api)
        qtbot.addWidget(self.page)

    def test_project_breakdown(self):
        tasks = [
            {"id": "1", "status": "completed", "_project_name": "Project A"},
            {"id": "2", "status": "completed", "_project_name": "Project A"},
            {"id": "3", "status": "error", "_project_name": "Project B"},
        ]
        self.page.update_stats(tasks)
        # Two projects → two rows
        assert self.page._project_container.count() == 2

    def test_no_projects_shows_empty(self):
        self.page.update_stats([])
        assert self.page._project_container.count() == 1  # empty state label
