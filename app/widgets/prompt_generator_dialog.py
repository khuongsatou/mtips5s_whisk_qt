"""
Whisk Desktop — Prompt Generator Dialog.

Opens a dialog with custom prompt template + user idea,
with ChatGPT and Gemini buttons to generate prompt ideas.
"""
import urllib.parse
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QApplication,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl


DEFAULT_TEMPLATE = (
    "Kèm thêm câu với ý tưởng bên dưới của tôi "
    "hãy cho tôi 10 scene nối tiếp bằng tiếng anh:"
)


class PromptGeneratorDialog(QDialog):
    """Dialog to generate prompt ideas via AI services."""

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(translator.t("prompt_gen.title"))
        self.setMinimumSize(520, 420)
        self.setObjectName("prompt_generator_dialog")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel(self.translator.t("prompt_gen.title"))
        title.setObjectName("prompt_gen_title")
        title.setStyleSheet(
            "font-size: 18px; font-weight: 700; padding-bottom: 4px;"
        )
        layout.addWidget(title)

        # Custom prompt template
        template_label = QLabel(f"📝 {self.translator.t('prompt_gen.template_label')}")
        template_label.setObjectName("config_label")
        layout.addWidget(template_label)

        self._template_input = QTextEdit()
        self._template_input.setObjectName("config_prompt")
        self._template_input.setPlainText(DEFAULT_TEMPLATE)
        self._template_input.setMaximumHeight(80)
        layout.addWidget(self._template_input)

        # User idea input
        idea_label = QLabel(f"💡 {self.translator.t('prompt_gen.idea_label')}")
        idea_label.setObjectName("config_label")
        layout.addWidget(idea_label)

        self._idea_input = QTextEdit()
        self._idea_input.setObjectName("config_prompt")
        self._idea_input.setPlaceholderText(
            self.translator.t("prompt_gen.idea_placeholder")
        )
        self._idea_input.setMinimumHeight(100)
        layout.addWidget(self._idea_input)

        layout.addStretch()

        # AI buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        gpt_btn = QPushButton("🤖 ChatGPT")
        gpt_btn.setObjectName("toolbar_run_button")
        gpt_btn.setCursor(Qt.PointingHandCursor)
        gpt_btn.setFixedHeight(40)
        gpt_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10a37f, stop:1 #1a7f64);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
                padding: 8px 20px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a7f64, stop:1 #10a37f);
            }
            QPushButton:pressed { background: #0d8c6d; }
        """)
        gpt_btn.clicked.connect(lambda: self._open_ai("chatgpt"))
        btn_row.addWidget(gpt_btn, 1)

        gemini_btn = QPushButton("✨ Gemini")
        gemini_btn.setObjectName("toolbar_run_button")
        gemini_btn.setCursor(Qt.PointingHandCursor)
        gemini_btn.setFixedHeight(40)
        gemini_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4285f4, stop:1 #6d5ce7);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
                padding: 8px 20px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d5ce7, stop:1 #4285f4);
            }
            QPushButton:pressed { background: #3b74d4; }
        """)
        gemini_btn.clicked.connect(lambda: self._open_ai("gemini"))
        btn_row.addWidget(gemini_btn, 1)

        layout.addLayout(btn_row)

    def _get_full_prompt(self) -> str:
        """Combine template + user idea."""
        template = self._template_input.toPlainText().strip()
        idea = self._idea_input.toPlainText().strip()
        if template and idea:
            return f"{template}\n\n{idea}"
        return template or idea

    def _open_ai(self, service: str):
        """Copy prompt to clipboard and open AI service."""
        full_text = self._get_full_prompt()
        if not full_text:
            return

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(full_text)

        # Open URL
        if service == "chatgpt":
            encoded = urllib.parse.quote(full_text, safe="")
            url = f"https://chatgpt.com/?prompt={encoded}"
        else:
            url = "https://gemini.google.com/"

        QDesktopServices.openUrl(QUrl(url))
