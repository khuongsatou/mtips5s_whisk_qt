"""
Tests for ToggleSwitch widget — state, animation, painting, custom colors.
"""
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPaintEvent, QPixmap
from app.widgets.toggle_switch import ToggleSwitch


class TestToggleSwitch:
    """Test ToggleSwitch behavior."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.switch = ToggleSwitch("Test Toggle")
        qtbot.addWidget(self.switch)

    def test_initial_unchecked(self):
        assert not self.switch.isChecked()

    def test_initial_position_zero(self):
        assert self.switch._position == 0.0

    def test_check_triggers_animation(self):
        self.switch.setChecked(True)
        assert self.switch.isChecked()
        assert self.switch._animation.endValue() == 1.0

    def test_uncheck_triggers_animation(self):
        self.switch.setChecked(True)
        self.switch._position = 1.0
        self.switch.setChecked(False)
        assert not self.switch.isChecked()
        assert self.switch._animation.endValue() == 0.0

    def test_text_label(self):
        assert self.switch.text() == "Test Toggle"

    def test_size_hint_with_text(self):
        size = self.switch.sizeHint()
        assert size.width() > self.switch._TRACK_W
        assert size.height() >= self.switch._TRACK_H

    def test_size_hint_without_text(self, qtbot):
        empty = ToggleSwitch("")
        qtbot.addWidget(empty)
        size = empty.sizeHint()
        assert size.width() == empty._TRACK_W + 4

    def test_minimum_size_hint_equals_size_hint(self):
        assert self.switch.minimumSizeHint() == self.switch.sizeHint()

    def test_set_track_colors(self):
        self.switch.set_track_colors("#FF0000", "#00FF00")
        assert self.switch._TRACK_OFF == QColor("#FF0000")
        assert self.switch._TRACK_ON == QColor("#00FF00")

    def test_hit_button_in_rect(self):
        center = self.switch.rect().center()
        assert self.switch.hitButton(center)

    def test_switch_position_property(self):
        self.switch._set_position(0.5)
        assert self.switch._get_position() == 0.5


class TestToggleSwitchPainting:
    """Test ToggleSwitch paint and rendering methods."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.switch = ToggleSwitch("Paint Test")
        qtbot.addWidget(self.switch)
        self.switch.setFixedSize(100, 30)

    def test_paint_event_unchecked(self):
        """paintEvent should not crash when unchecked (position=0)."""
        self.switch._position = 0.0
        pixmap = QPixmap(self.switch.size())
        self.switch.render(pixmap)
        # No crash = success

    def test_paint_event_checked(self):
        """paintEvent should not crash when checked (position=1)."""
        self.switch._position = 1.0
        pixmap = QPixmap(self.switch.size())
        self.switch.render(pixmap)

    def test_paint_event_midway(self):
        """paintEvent should handle intermediate positions (animation mid-point)."""
        self.switch._position = 0.5
        pixmap = QPixmap(self.switch.size())
        self.switch.render(pixmap)

    def test_paint_event_no_text(self, qtbot):
        """paintEvent should handle switch with no label text."""
        switch = ToggleSwitch("")
        qtbot.addWidget(switch)
        switch.setFixedSize(50, 24)
        pixmap = QPixmap(switch.size())
        switch.render(pixmap)

    def test_paint_event_custom_colors(self):
        """paintEvent should use custom colors without crash."""
        self.switch.set_track_colors("#FF6600", "#00CC44")
        self.switch._position = 0.7
        pixmap = QPixmap(self.switch.size())
        self.switch.render(pixmap)

    def test_hit_button_outside_rect(self):
        """Clicking outside the widget rect should not count."""
        outside = QPoint(-10, -10)
        assert not self.switch.hitButton(outside)

    def test_animation_state_change_stops_previous(self):
        """State change should stop the current animation before starting new."""
        self.switch._position = 0.0
        self.switch.setChecked(True)
        # Immediately toggle back before animation finishes
        self.switch.setChecked(False)
        assert self.switch._animation.endValue() == 0.0
