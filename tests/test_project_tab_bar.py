"""
Tests for ProjectTabBar — Chrome-style tab management.
"""
import pytest
from app.widgets.project_tab_bar import ProjectTabBar


class TestProjectTabBarInit:
    """Test initial state."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.bar = ProjectTabBar()
        qtbot.addWidget(self.bar)

    def test_no_tabs_initially(self):
        assert self.bar.tab_count() == 0

    def test_active_index_is_minus_one(self):
        assert self.bar.active_index() == -1

    def test_has_add_button(self):
        assert self.bar._add_btn is not None
        assert self.bar._add_btn.text() == "+"


class TestProjectTabBarAddTab:
    """Test adding tabs."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.bar = ProjectTabBar()
        self.qtbot = qtbot
        qtbot.addWidget(self.bar)

    def test_add_tab_returns_index(self):
        idx = self.bar.add_tab("f1", "Project A")
        assert idx == 0

    def test_add_tab_increments_count(self):
        self.bar.add_tab("f1", "A")
        self.bar.add_tab("f2", "B")
        assert self.bar.tab_count() == 2

    def test_add_tab_auto_selects(self):
        self.bar.add_tab("f1", "A")
        assert self.bar.active_index() == 0

    def test_add_second_tab_selects_it(self):
        self.bar.add_tab("f1", "A")
        self.bar.add_tab("f2", "B")
        assert self.bar.active_index() == 1

    def test_add_tab_emits_tab_changed(self):
        with self.qtbot.waitSignal(self.bar.tab_changed, timeout=500) as blocker:
            self.bar.add_tab("f1", "A")
        assert blocker.args == [0]


class TestProjectTabBarRemoveTab:
    """Test removing tabs."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.bar = ProjectTabBar()
        qtbot.addWidget(self.bar)
        self.bar.add_tab("f1", "A")
        self.bar.add_tab("f2", "B")
        self.bar.add_tab("f3", "C")

    def test_remove_tab_decrements_count(self):
        self.bar.remove_tab(1)
        assert self.bar.tab_count() == 2

    def test_remove_invalid_index_noop(self):
        self.bar.remove_tab(99)
        assert self.bar.tab_count() == 3

    def test_remove_negative_index_noop(self):
        self.bar.remove_tab(-1)
        assert self.bar.tab_count() == 3

    def test_remove_all_tabs(self):
        self.bar.remove_tab(0)
        self.bar.remove_tab(0)
        self.bar.remove_tab(0)
        assert self.bar.tab_count() == 0
        assert self.bar.active_index() == -1


class TestProjectTabBarSetActive:
    """Test setting active tab."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.bar = ProjectTabBar()
        self.qtbot = qtbot
        qtbot.addWidget(self.bar)
        self.bar.add_tab("f1", "A")
        self.bar.add_tab("f2", "B")

    def test_set_active_tab(self):
        self.bar.set_active_tab(0)
        assert self.bar.active_index() == 0

    def test_set_active_invalid_noop(self):
        self.bar.set_active_tab(99)
        assert self.bar.active_index() == 1  # unchanged

    def test_set_active_emits_signal(self):
        with self.qtbot.waitSignal(self.bar.tab_changed, timeout=500) as blocker:
            self.bar.set_active_tab(0)
        assert blocker.args == [0]


class TestProjectTabBarData:
    """Test data accessors."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.bar = ProjectTabBar()
        qtbot.addWidget(self.bar)
        self.bar.add_tab("f1", "Alpha")
        self.bar.add_tab("f2", "Beta")

    def test_tab_data(self):
        data = self.bar.tab_data(0)
        assert data == {"flow_id": "f1", "flow_name": "Alpha"}

    def test_tab_data_invalid(self):
        assert self.bar.tab_data(99) is None

    def test_all_tabs_data(self):
        result = self.bar.all_tabs_data()
        assert len(result) == 2
        assert result[0]["flow_id"] == "f1"
        assert result[1]["flow_name"] == "Beta"

    def test_find_tab_by_flow_id(self):
        assert self.bar.find_tab_by_flow_id("f2") == 1

    def test_find_tab_not_found(self):
        assert self.bar.find_tab_by_flow_id("f99") == -1


class TestProjectTabBarNewTabSignal:
    """Test + button signal."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.bar = ProjectTabBar()
        self.qtbot = qtbot
        qtbot.addWidget(self.bar)

    def test_add_btn_emits_new_tab_requested(self):
        with self.qtbot.waitSignal(self.bar.new_tab_requested, timeout=500):
            self.bar._add_btn.click()
