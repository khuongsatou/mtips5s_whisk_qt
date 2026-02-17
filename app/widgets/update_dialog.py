"""
Whisk Desktop — Software Update Dialog.

Modal dialog that checks for updates, shows changelog,
and offers a download button.
"""
import threading
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QWidget,
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from app.version import __version__
from app.api.update_api import check_for_update


class _UpdateSignals(QObject):
    """Bridge to emit results from background thread."""
    result = Signal(dict)


class UpdateDialog(QDialog):
    """Dialog to check for software updates and display results."""

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(translator.t("update.title"))
        self.setMinimumSize(480, 400)
        self.setObjectName("update_dialog")
        self._signals = _UpdateSignals()
        self._signals.result.connect(self._on_result)
        self._download_url = ""
        self._setup_ui()
        self._start_check()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        # Title
        title = QLabel(f"🔄 {self.translator.t('update.title')}")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        # Version info row
        ver_row = QHBoxLayout()
        ver_row.setSpacing(16)

        # Current version card
        cur_card = self._version_card(
            self.translator.t("update.current"), __version__, "#6B7280"
        )
        ver_row.addWidget(cur_card, 1)

        # Arrow
        arrow = QLabel("→")
        arrow.setStyleSheet("font-size: 24px; font-weight: 700; color: #6B7280;")
        arrow.setAlignment(Qt.AlignCenter)
        ver_row.addWidget(arrow)

        # Latest version card (updated after check)
        self._latest_card_label = QLabel("...")
        self._latest_card_label.setStyleSheet(
            "font-size: 20px; font-weight: 800; color: #6B7280;"
        )
        self._latest_card_label.setAlignment(Qt.AlignCenter)
        self._latest_card_title = QLabel(self.translator.t("update.latest"))
        self._latest_card_title.setStyleSheet(
            "font-size: 11px; color: #9CA3AF; font-weight: 600;"
        )
        self._latest_card_title.setAlignment(Qt.AlignCenter)

        latest_card = QWidget()
        latest_card.setStyleSheet(
            "background: #1f2937; border-radius: 10px; padding: 12px;"
        )
        lc_layout = QVBoxLayout(latest_card)
        lc_layout.setContentsMargins(12, 10, 12, 10)
        lc_layout.setSpacing(2)
        lc_layout.addWidget(self._latest_card_title)
        lc_layout.addWidget(self._latest_card_label)
        ver_row.addWidget(latest_card, 1)

        layout.addLayout(ver_row)

        # Status label (checking / up to date / error)
        self._status_label = QLabel(f"⏳ {self.translator.t('update.checking')}")
        self._status_label.setObjectName("config_label")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(
            "font-size: 13px; color: #9CA3AF; padding: 8px 0;"
        )
        layout.addWidget(self._status_label)

        # Changelog area
        changelog_label = QLabel(f"📝 {self.translator.t('update.changelog')}")
        changelog_label.setObjectName("config_label")
        layout.addWidget(changelog_label)

        self._changelog_text = QTextEdit()
        self._changelog_text.setObjectName("config_prompt")
        self._changelog_text.setReadOnly(True)
        self._changelog_text.setPlaceholderText("—")
        self._changelog_text.setMinimumHeight(100)
        layout.addWidget(self._changelog_text, 1)

        # Download button (hidden initially)
        self._download_btn = QPushButton(
            f"⬇️ {self.translator.t('update.download')}"
        )
        self._download_btn.setCursor(Qt.PointingHandCursor)
        self._download_btn.setFixedHeight(42)
        self._download_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B5CF6, stop:1 #6D28D9);
                color: white; border: none; border-radius: 10px;
                font-size: 14px; font-weight: 700; padding: 8px 20px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6D28D9, stop:1 #8B5CF6);
            }
            QPushButton:pressed { background: #5B21B6; }
        """)
        self._download_btn.clicked.connect(self._on_download)
        self._download_btn.setVisible(False)
        layout.addWidget(self._download_btn)

    @staticmethod
    def _version_card(title: str, version: str, color: str) -> QWidget:
        card = QWidget()
        card.setStyleSheet(
            "background: #1f2937; border-radius: 10px; padding: 12px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(12, 10, 12, 10)
        vl.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet("font-size: 11px; color: #9CA3AF; font-weight: 600;")
        t.setAlignment(Qt.AlignCenter)
        vl.addWidget(t)
        v = QLabel(f"v{version}")
        v.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color};")
        v.setAlignment(Qt.AlignCenter)
        vl.addWidget(v)
        return card

    def _start_check(self):
        """Run update check in background thread."""
        def _worker():
            result = check_for_update(__version__)
            self._signals.result.emit(result)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_result(self, result: dict):
        """Handle update check result on main thread."""
        error = result.get("error")
        if error:
            self._status_label.setText(
                f"❌ {self.translator.t('update.error')}"
            )
            self._status_label.setStyleSheet(
                "font-size: 13px; color: #EF4444; padding: 8px 0;"
            )
            self._latest_card_label.setText("—")
            return

        latest = result["latest_version"]
        has_update = result["has_update"]
        self._download_url = result.get("download_url", "")
        changelog = result.get("changelog", "")

        self._latest_card_label.setText(f"v{latest}")

        if has_update:
            self._latest_card_label.setStyleSheet(
                "font-size: 20px; font-weight: 800; color: #10B981;"
            )
            self._status_label.setText(
                f"🎉 {self.translator.t('update.available')}"
            )
            self._status_label.setStyleSheet(
                "font-size: 14px; color: #10B981; font-weight: 700; padding: 8px 0;"
            )
            if self._download_url:
                self._download_btn.setVisible(True)
        else:
            self._latest_card_label.setStyleSheet(
                "font-size: 20px; font-weight: 800; color: #6B7280;"
            )
            self._status_label.setText(
                f"✅ {self.translator.t('update.up_to_date')}"
            )
            self._status_label.setStyleSheet(
                "font-size: 14px; color: #10B981; font-weight: 600; padding: 8px 0;"
            )

        if changelog:
            self._changelog_text.setPlainText(changelog)

    def _on_download(self):
        """Open download URL in default browser."""
        if self._download_url:
            QDesktopServices.openUrl(QUrl(self._download_url))
