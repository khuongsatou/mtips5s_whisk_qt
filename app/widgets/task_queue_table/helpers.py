"""
Whisk Desktop — Task Queue Table Helper Widgets.

Small utility classes used by TaskQueueTable: ClickableLabel,
ImagePreviewDialog, and PromptDelegate.
"""
from PySide6.QtWidgets import (
    QLabel, QPushButton, QDialog, QScrollArea, QFileDialog,
    QHBoxLayout, QVBoxLayout, QWidget,
    QStyledItemDelegate, QTextEdit,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
import os
import shutil


class ClickableLabel(QLabel):
    """QLabel that emits a signal when clicked."""
    clicked = Signal(str)  # image_path

    def __init__(self, image_path: str = "", parent=None):
        super().__init__(parent)
        self._image_path = image_path
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._image_path:
            self.clicked.emit(self._image_path)
        super().mousePressEvent(event)


class ImagePreviewDialog(QDialog):
    """Modal dialog to preview an image at full size."""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Preview")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModal(True)
        self.setMinimumSize(480, 400)

        self._image_path = image_path

        # Get screen size for sensible dialog dimensions
        screen_size = self.screen().availableGeometry()
        max_w = int(screen_size.width() * 0.85)
        max_h = int(screen_size.height() * 0.85)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scrollable image area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setStyleSheet("background: #1a1a2e; border: none;")

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                max_w, max_h - 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            img_label.setPixmap(scaled)
        else:
            img_label.setText("Could not load image")
            img_label.setStyleSheet("color: #999; font-size: 16px;")

        scroll.setWidget(img_label)
        layout.addWidget(scroll, 1)

        # Bottom toolbar (solid background, no overlap)
        toolbar = QWidget()
        toolbar.setFixedHeight(52)
        toolbar.setStyleSheet("""
            QWidget {
                background: #2D2D44;
                border-top: 1px solid #3D3D5C;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(10)

        # Download button
        dl_btn = QPushButton("💾 Download")
        dl_btn.setCursor(Qt.PointingHandCursor)
        dl_btn.setFixedSize(140, 36)
        dl_btn.setStyleSheet("""
            QPushButton {
                background: #7C3AED;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background: #6D28D9; }
            QPushButton:pressed { background: #5B21B6; }
        """)
        dl_btn.clicked.connect(self._on_download)
        toolbar_layout.addWidget(dl_btn)

        toolbar_layout.addStretch()

        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(100, 36)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background: #DC2626; }
            QPushButton:pressed { background: #B91C1C; }
        """)
        close_btn.clicked.connect(self.close)
        toolbar_layout.addWidget(close_btn)

        layout.addWidget(toolbar)

        self.resize(min(pixmap.width() + 40, max_w), min(pixmap.height() + 100, max_h))

    def _on_download(self):
        """Save the previewed image to a user-chosen location."""
        if not self._image_path or not os.path.isfile(self._image_path):
            return
        basename = os.path.basename(self._image_path)
        default_path = os.path.join(os.path.expanduser("~/Downloads"), basename)
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save Image", default_path,
            "Images (*.png *.jpg *.jpeg *.webp);;All Files (*)",
        )
        if dest:
            shutil.copy2(self._image_path, dest)


class PromptDelegate(QStyledItemDelegate):
    """Custom delegate that uses a QTextEdit for multi-line prompt editing."""

    def createEditor(self, parent, option, index):
        editor = QTextEdit(parent)
        editor.setObjectName("prompt_editor")
        editor.setAcceptRichText(False)
        return editor

    def setEditorData(self, editor, index):
        text = index.data(Qt.DisplayRole) or ""
        editor.setPlainText(text)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.toPlainText(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
