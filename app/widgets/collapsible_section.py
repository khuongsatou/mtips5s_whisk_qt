"""
Whisk Desktop — Collapsible Section Widget.

A reusable section with a clickable header that toggles visibility
of its content area. Used in ConfigPanel and other dense layouts.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QSizePolicy,
    QFrame, QPushButton,
)
from PySide6.QtCore import Signal, Qt


class CollapsibleSection(QWidget):
    """A section with a clickable header that collapses/expands its content."""

    toggled = Signal(bool)  # Emits True when expanded, False when collapsed

    def __init__(self, title: str = "", expanded: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("collapsible_section")
        self._title = title
        self._expanded = expanded
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Header (clickable toggle) — use button text directly ---
        self._header = QPushButton()
        self._header.setObjectName("collapsible_header")
        self._header.setCursor(Qt.PointingHandCursor)
        self._header.clicked.connect(self.toggle)
        self._header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self._header)

        # --- Content area ---
        self._content = QWidget()
        self._content.setObjectName("collapsible_content")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 4, 0, 4)
        self._content_layout.setSpacing(6)

        main_layout.addWidget(self._content)

        # Set initial state
        self._update_state()

    def add_widget(self, widget: QWidget):
        """Add a widget to the collapsible content area."""
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Add a layout to the collapsible content area."""
        self._content_layout.addLayout(layout)

    def toggle(self):
        """Toggle collapsed/expanded state."""
        self._expanded = not self._expanded
        self._update_state()
        self.toggled.emit(self._expanded)

    def set_expanded(self, expanded: bool):
        """Set the expanded state."""
        if expanded != self._expanded:
            self._expanded = expanded
            self._update_state()
            self.toggled.emit(self._expanded)

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    def set_title(self, title: str):
        """Update the section title."""
        self._title = title
        self._update_state()

    def _update_state(self):
        """Update header text and content visibility."""
        arrow = "▼" if self._expanded else "▶"
        self._header.setText(f"  {arrow}  {self._title}")
        self._content.setVisible(self._expanded)
