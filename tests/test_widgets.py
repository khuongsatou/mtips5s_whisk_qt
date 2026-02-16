"""
Tests for UI Widgets (updated for Image Creator).
"""
import pytest
from PySide6.QtCore import Qt
from app.i18n.translator import Translator
from app.theme.theme_manager import ThemeManager
from app.widgets.sidebar import Sidebar
from app.widgets.header import Header
from app.widgets.status_badge import StatusBadge
from app.widgets.reference_image_grid import ReferenceImageGrid


class TestSidebar:
    """Test suite for the Sidebar widget."""

    def test_sidebar_has_nav_buttons(self, qtbot):
        """Sidebar should have buttons for each nav item."""
        translator = Translator()
        sidebar = Sidebar(translator)
        qtbot.addWidget(sidebar)

        assert "image_creator" in sidebar._buttons
        assert "settings" in sidebar._buttons

    def test_sidebar_default_active_is_image_creator(self, qtbot):
        """Default active page should be image_creator."""
        translator = Translator()
        sidebar = Sidebar(translator)
        qtbot.addWidget(sidebar)

        assert sidebar._active_page == "image_creator"

    def test_sidebar_click_changes_active(self, qtbot):
        """Clicking a nav button should change active page."""
        translator = Translator()
        sidebar = Sidebar(translator)
        qtbot.addWidget(sidebar)

        with qtbot.waitSignal(sidebar.page_changed, timeout=1000) as blocker:
            qtbot.mouseClick(sidebar._buttons["settings"], Qt.LeftButton)
        assert blocker.args == ["settings"]
        assert sidebar._active_page == "settings"

    def test_sidebar_set_active_page(self, qtbot):
        """Programmatic set_active_page should update state."""
        translator = Translator()
        sidebar = Sidebar(translator)
        qtbot.addWidget(sidebar)

        sidebar.set_active_page("settings")
        assert sidebar._active_page == "settings"

    def test_sidebar_retranslate(self, qtbot):
        """Language change should update button text when expanded."""
        translator = Translator()
        sidebar = Sidebar(translator)
        qtbot.addWidget(sidebar)

        # Expand sidebar so retranslate sets text labels
        if sidebar._collapsed:
            sidebar.toggle_collapse()

        translator.set_language("vi")
        btn = sidebar._buttons["image_creator"]
        assert "Tạo Ảnh" in btn.text()


class TestHeader:
    """Test suite for the Header widget."""

    def test_header_has_theme_button(self, qtbot):
        """Header should have a theme toggle button."""
        translator = Translator()
        theme = ThemeManager()
        header = Header(translator, theme)
        qtbot.addWidget(header)

        assert header._theme_btn is not None

    def test_header_theme_toggle_emits_signal(self, qtbot):
        """Clicking theme toggle should emit theme_toggled signal."""
        translator = Translator()
        theme = ThemeManager()
        header = Header(translator, theme)
        qtbot.addWidget(header)

        with qtbot.waitSignal(header.theme_toggled, timeout=1000):
            qtbot.mouseClick(header._theme_btn, Qt.LeftButton)

    def test_header_set_page_title(self, qtbot):
        """set_page_title should update the title label."""
        translator = Translator()
        theme = ThemeManager()
        header = Header(translator, theme)
        qtbot.addWidget(header)

        header.set_page_title("Test Page")
        assert header._page_title.text() == "Test Page"


class TestStatusBadge:
    """Test suite for the StatusBadge widget."""

    def test_badge_completed(self, qtbot):
        """Completed badge should have correct object name."""
        translator = Translator()
        badge = StatusBadge("completed", translator)
        qtbot.addWidget(badge)
        assert badge.objectName() == "badge_completed"

    def test_badge_pending(self, qtbot):
        """Pending badge should have correct object name."""
        translator = Translator()
        badge = StatusBadge("pending", translator)
        qtbot.addWidget(badge)
        assert badge.objectName() == "badge_pending"

    def test_badge_set_status(self, qtbot):
        """set_status should update the badge."""
        translator = Translator()
        badge = StatusBadge("pending", translator)
        qtbot.addWidget(badge)
        badge.set_status("completed")
        assert badge.objectName() == "badge_completed"


class TestReferenceImageGrid:
    """Test suite for the ReferenceImageGrid widget."""

    def test_grid_has_three_columns(self, qtbot):
        """Grid should have 3 columns: Title, Scene, Style."""
        grid = ReferenceImageGrid()
        qtbot.addWidget(grid)
        assert len(grid._columns) == 3
        assert "Title" in grid._columns
        assert "Scene" in grid._columns
        assert "Style" in grid._columns

    def test_grid_columns_start_with_one_slot(self, qtbot):
        """Each column starts with 1 image slot."""
        grid = ReferenceImageGrid()
        qtbot.addWidget(grid)
        for col in grid._columns.values():
            assert len(col._slots) == 1

    def test_grid_set_paths_auto_expands(self, qtbot):
        """set_paths should auto-expand slots when needed."""
        grid = ReferenceImageGrid()
        qtbot.addWidget(grid)
        col = grid._columns["Title"]
        col.set_paths(["a.png", "b.png", "c.png"])
        assert len(col._slots) == 3

    def test_grid_set_paths_by_category(self, qtbot):
        """set_paths_by_category should handle case-insensitive keys."""
        grid = ReferenceImageGrid()
        qtbot.addWidget(grid)
        grid.set_paths_by_category({"title": ["a.png"], "scene": ["b.png"]})
        assert len(grid._columns["Title"]._slots) >= 1
        assert len(grid._columns["Scene"]._slots) >= 1

    def test_grid_get_paths_empty(self, qtbot):
        """Empty grid should return no paths."""
        grid = ReferenceImageGrid()
        qtbot.addWidget(grid)
        assert grid.get_paths() == []

    def test_grid_clear_all(self, qtbot):
        """clear_all should remove all images."""
        grid = ReferenceImageGrid()
        qtbot.addWidget(grid)
        grid.clear_all()
        assert grid.get_paths() == []

    def test_grid_max_five_slots(self, qtbot):
        """Columns should not exceed 5 slots."""
        grid = ReferenceImageGrid()
        qtbot.addWidget(grid)
        col = grid._columns["Title"]
        col.set_paths(["1.png", "2.png", "3.png", "4.png", "5.png", "6.png"])
        assert len(col._slots) == 5
