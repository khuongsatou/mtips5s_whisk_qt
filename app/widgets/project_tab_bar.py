"""
Whisk Desktop — Project Tab Bar Widget.

Chrome-style tab bar where each project is a tab.
Supports close button per tab and a "+" button to add new tabs.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QSizePolicy, QLabel,
)
from PySide6.QtCore import Signal, Qt


class ProjectTabBar(QWidget):
    """Chrome-style tab bar for project tabs."""

    tab_changed = Signal(int)          # index of newly selected tab
    tab_close_requested = Signal(int)  # index of tab to close
    new_tab_requested = Signal()       # "+" button clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("project_tab_bar")
        self._tabs: list[dict] = []  # {btn, close_btn, flow_id, flow_name}
        self._active_index = -1
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 0, 8, 0)
        self._layout.setSpacing(0)

        # Stretch at end pushes tabs left
        self._stretch_index = None

        # "+" button
        self._add_btn = QPushButton("+")
        self._add_btn.setObjectName("tab_add_btn")
        self._add_btn.setFixedSize(32, 32)
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.setToolTip("New project tab")
        self._add_btn.clicked.connect(self.new_tab_requested.emit)

        self._layout.addWidget(self._add_btn)
        self._layout.addStretch(1)

    def add_tab(self, flow_id: str, flow_name: str) -> int:
        """Add a new tab. Returns the index of the new tab."""
        index = len(self._tabs)

        # Tab button (clickable label area)
        tab_widget = QWidget()
        tab_widget.setObjectName("project_tab")
        tab_widget.setCursor(Qt.PointingHandCursor)

        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(12, 4, 4, 4)
        tab_layout.setSpacing(4)

        name_label = QLabel(flow_name or f"Project {flow_id}")
        name_label.setObjectName("tab_name_label")
        name_label.setAlignment(Qt.AlignVCenter)
        tab_layout.addWidget(name_label)

        close_btn = QPushButton("×")
        close_btn.setObjectName("tab_close_btn")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setToolTip("Close tab")
        close_btn.clicked.connect(lambda: self._on_close(index))
        tab_layout.addWidget(close_btn)

        # Install click handler on the tab widget
        tab_widget.mousePressEvent = lambda ev, idx=index: self._on_tab_click(idx)

        # Insert before the "+" button
        insert_pos = self._layout.indexOf(self._add_btn)
        self._layout.insertWidget(insert_pos, tab_widget)

        self._tabs.append({
            "widget": tab_widget,
            "name_label": name_label,
            "close_btn": close_btn,
            "flow_id": flow_id,
            "flow_name": flow_name,
        })

        # Auto-select the new tab
        self.set_active_tab(index)
        return index

    def remove_tab(self, index: int):
        """Remove a tab by index."""
        if index < 0 or index >= len(self._tabs):
            return

        tab_data = self._tabs.pop(index)
        tab_data["widget"].setParent(None)
        tab_data["widget"].deleteLater()

        # Re-bind click/close handlers for shifted indices
        for i, t in enumerate(self._tabs):
            t["widget"].mousePressEvent = lambda ev, idx=i: self._on_tab_click(idx)
            t["close_btn"].clicked.disconnect()
            t["close_btn"].clicked.connect(lambda checked=False, idx=i: self._on_close(idx))

        # Adjust active index
        if len(self._tabs) == 0:
            self._active_index = -1
        elif self._active_index >= len(self._tabs):
            self.set_active_tab(len(self._tabs) - 1)
        elif self._active_index == index:
            # Was the closed tab active? Select neighbor
            new_idx = min(index, len(self._tabs) - 1)
            self.set_active_tab(new_idx)
        elif self._active_index > index:
            self._active_index -= 1
            self._update_styles()

    def set_active_tab(self, index: int):
        """Set the active tab by index."""
        if index < 0 or index >= len(self._tabs):
            return
        self._active_index = index
        self._update_styles()
        self.tab_changed.emit(index)

    def _on_tab_click(self, index: int):
        """Handle tab click."""
        if index != self._active_index:
            self.set_active_tab(index)

    def _on_close(self, index: int):
        """Handle close button click."""
        self.tab_close_requested.emit(index)

    def _update_styles(self):
        """Update active/inactive tab styling via properties."""
        for i, t in enumerate(self._tabs):
            is_active = (i == self._active_index)
            t["widget"].setProperty("active", is_active)
            t["widget"].style().unpolish(t["widget"])
            t["widget"].style().polish(t["widget"])
            t["name_label"].setProperty("active", is_active)
            t["name_label"].style().unpolish(t["name_label"])
            t["name_label"].style().polish(t["name_label"])

    def tab_count(self) -> int:
        """Return number of open tabs."""
        return len(self._tabs)

    def active_index(self) -> int:
        """Return the active tab index."""
        return self._active_index

    def tab_data(self, index: int) -> dict | None:
        """Get tab data (flow_id, flow_name) for a given index."""
        if 0 <= index < len(self._tabs):
            return {
                "flow_id": self._tabs[index]["flow_id"],
                "flow_name": self._tabs[index]["flow_name"],
            }
        return None

    def all_tabs_data(self) -> list[dict]:
        """Get data for all tabs (for persistence)."""
        return [
            {"flow_id": t["flow_id"], "flow_name": t["flow_name"]}
            for t in self._tabs
        ]

    def find_tab_by_flow_id(self, flow_id: str) -> int:
        """Find tab index by flow_id. Returns -1 if not found."""
        for i, t in enumerate(self._tabs):
            if str(t["flow_id"]) == str(flow_id):
                return i
        return -1
