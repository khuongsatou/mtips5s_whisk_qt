"""
Whisk Desktop — Reference Image Grid Widget.

3-column reference image grid: Title, Scene, Style.
Each column has up to 5 image slots.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFileDialog, QMenu, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QAction


class ImageSlot(QPushButton):
    """A single clickable image slot in the reference grid."""

    image_set = Signal(int, str)      # slot_index, file_path
    image_removed = Signal(int)       # slot_index

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self._index = index
        self._image_path = ""
        self.setObjectName("ref_image_slot")
        self.setFixedSize(42, 42)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setText("+")
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._on_click)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _on_click(self):
        """Open file dialog to pick an image."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp);;All Files (*)"
        )
        if path:
            self._set_image(path)

    def _set_image(self, path: str):
        """Set the image for this slot."""
        self._image_path = path
        pixmap = QPixmap(path).scaled(
            38, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setIcon(pixmap)
        self.setIconSize(pixmap.size())
        self.setText("")
        self.image_set.emit(self._index, path)

    def _show_context_menu(self, pos):
        """Show context menu to remove image."""
        if not self._image_path:
            return
        menu = QMenu(self)
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self._remove_image)
        menu.addAction(remove_action)
        menu.exec(self.mapToGlobal(pos))

    def _remove_image(self):
        """Clear this slot."""
        self._image_path = ""
        self.setIcon(QPixmap())
        self.setText("+")
        self.image_removed.emit(self._index)

    @property
    def image_path(self) -> str:
        return self._image_path

    def set_path(self, path: str):
        """Set image path programmatically."""
        if path:
            self._set_image(path)
        else:
            self._remove_image()


class ImageColumn(QWidget):
    """A single column with a header label and up to MAX_SLOTS image slots."""

    images_changed = Signal()
    MAX_SLOTS = 1

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("ref_image_column")
        self._slots: list[ImageSlot] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # Column header
        header = QLabel(title)
        header.setObjectName("ref_column_header")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Image slots grid
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setContentsMargins(2, 2, 2, 2)
        self._grid.setSpacing(4)

        for i in range(self.MAX_SLOTS):
            self._add_slot(i)

        layout.addWidget(self._grid_widget)

        # Add button
        self._add_btn = QPushButton("+")
        self._add_btn.setObjectName("ref_add_slot_btn")
        self._add_btn.setFixedSize(42, 20)
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.setToolTip("Add image slot")
        self._add_btn.clicked.connect(self._on_add_slot)
        layout.addWidget(self._add_btn, 0, Qt.AlignCenter)

        layout.addStretch()

    def _add_slot(self, index: int):
        """Create and add a new image slot."""
        slot = ImageSlot(index, self)
        slot.image_set.connect(lambda *a: self.images_changed.emit())
        slot.image_removed.connect(lambda *a: self.images_changed.emit())
        row = index // 2
        col = index % 2
        self._grid.addWidget(slot, row, col)
        self._slots.append(slot)

    def _on_add_slot(self):
        """Add a new image slot (max 5)."""
        if len(self._slots) >= 5:
            return
        self._add_slot(len(self._slots))
        if len(self._slots) >= 5:
            self._add_btn.hide()

    def get_paths(self) -> list[str]:
        return [s.image_path for s in self._slots if s.image_path]

    def set_paths(self, paths: list[str]):
        # Auto-expand slots if needed (up to 5)
        while len(self._slots) < len(paths) and len(self._slots) < 5:
            self._add_slot(len(self._slots))
        if len(self._slots) >= 5:
            self._add_btn.hide()

        for i, slot in enumerate(self._slots):
            if i < len(paths) and paths[i]:
                slot.set_path(paths[i])
            else:
                slot.set_path("")

    def clear_all(self):
        for slot in self._slots:
            slot.set_path("")


class ReferenceImageGrid(QWidget):
    """3-column reference image grid: Title, Scene, Style."""

    images_changed = Signal(list)  # Emits dict-like list of all paths

    CATEGORIES = ["Title", "Scene", "Style"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ref_image_grid")
        self._columns: dict[str, ImageColumn] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        for category in self.CATEGORIES:
            col = ImageColumn(category, self)
            col.images_changed.connect(self._on_images_changed)
            layout.addWidget(col, 1)
            self._columns[category] = col

    def _on_images_changed(self):
        """Emit updated paths."""
        self.images_changed.emit(self.get_paths())

    def get_paths(self) -> list[str]:
        """Get all non-empty paths across all columns."""
        paths = []
        for cat in self.CATEGORIES:
            paths.extend(self._columns[cat].get_paths())
        return paths

    def get_paths_by_category(self) -> dict[str, list[str]]:
        """Get paths organized by category."""
        return {cat: self._columns[cat].get_paths() for cat in self.CATEGORIES}

    def set_paths(self, paths: list[str]):
        """Set paths sequentially across columns (5 per column)."""
        for i, cat in enumerate(self.CATEGORIES):
            start = i * ImageColumn.MAX_SLOTS
            end = start + ImageColumn.MAX_SLOTS
            self._columns[cat].set_paths(paths[start:end])

    def set_paths_by_category(self, paths_dict: dict[str, list[str]]):
        """Set paths by category name (case-insensitive)."""
        for cat, paths in paths_dict.items():
            key = cat.capitalize()
            if key in self._columns:
                self._columns[key].set_paths(paths)

    def clear_all(self):
        """Clear all columns."""
        for col in self._columns.values():
            col.clear_all()
