"""
Tests for CollapsibleSection widget — toggle, expand/collapse, signals.
"""
import pytest
from app.widgets.collapsible_section import CollapsibleSection


class TestCollapsibleSection:
    """Test CollapsibleSection behavior."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.section = CollapsibleSection("Test Section", expanded=True)
        qtbot.addWidget(self.section)

    def test_initial_expanded(self):
        assert self.section.is_expanded
        assert not self.section._content.isHidden()

    def test_initial_title_in_header(self):
        assert "Test Section" in self.section._header.text()

    def test_header_shows_down_arrow_when_expanded(self):
        assert "▼" in self.section._header.text()

    def test_toggle_collapses(self, qtbot):
        with qtbot.waitSignal(self.section.toggled, timeout=1000):
            self.section.toggle()
        assert not self.section.is_expanded
        assert self.section._content.isHidden()

    def test_toggle_shows_right_arrow_when_collapsed(self):
        self.section.toggle()
        assert "▶" in self.section._header.text()

    def test_toggle_twice_restores(self, qtbot):
        self.section.toggle()
        self.section.toggle()
        assert self.section.is_expanded
        assert not self.section._content.isHidden()

    def test_set_expanded_false(self, qtbot):
        with qtbot.waitSignal(self.section.toggled, timeout=1000):
            self.section.set_expanded(False)
        assert not self.section.is_expanded

    def test_set_expanded_same_state_no_signal(self, qtbot):
        # Already expanded, setting expanded=True should not emit
        spy_count_before = 0
        signals = []
        self.section.toggled.connect(lambda v: signals.append(v))
        self.section.set_expanded(True)
        assert len(signals) == 0

    def test_set_title(self):
        self.section.set_title("New Title")
        assert "New Title" in self.section._header.text()

    def test_add_widget(self, qtbot):
        from PySide6.QtWidgets import QLabel
        label = QLabel("Test Label")
        self.section.add_widget(label)
        assert self.section._content_layout.count() >= 1


class TestCollapsibleSectionStartCollapsed:
    """Test CollapsibleSection created in collapsed state."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.section = CollapsibleSection("Collapsed", expanded=False)
        qtbot.addWidget(self.section)

    def test_starts_collapsed(self):
        assert not self.section.is_expanded
        assert self.section._content.isHidden()

    def test_starts_with_right_arrow(self):
        assert "▶" in self.section._header.text()

    def test_toggle_expands(self, qtbot):
        self.section.toggle()
        assert self.section.is_expanded
        assert not self.section._content.isHidden()
