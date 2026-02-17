"""
Whisk Desktop — Prompt Generator Dialog.

Opens a dialog with custom prompt template + user idea,
with ChatGPT and Gemini buttons to generate prompt ideas.
Includes a saved-prompts table persisted to ~/.whisk_saved_prompts.json.
"""
import json
import os
import urllib.parse
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QApplication, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl


DEFAULT_TEMPLATE = (
    "Kèm thêm câu với ý tưởng bên dưới của tôi "
    "hãy cho tôi 10 scene nối tiếp bằng tiếng anh:"
)

SAVED_PROMPTS_PATH = os.path.join(os.path.expanduser("~"), ".whisk_saved_prompts.json")


def _load_saved_prompts() -> list[dict]:
    """Load saved prompts from JSON file."""
    try:
        with open(SAVED_PROMPTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_prompts(prompts: list[dict]):
    """Save prompts list to JSON file."""
    with open(SAVED_PROMPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)


class PromptGeneratorDialog(QDialog):
    """Dialog to generate prompt ideas via AI services."""

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(translator.t("prompt_gen.title"))
        self.setMinimumSize(640, 620)
        self.setObjectName("prompt_generator_dialog")
        self._setup_ui()
        self._load_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(10)

        # Title
        title = QLabel(self.translator.t("prompt_gen.title"))
        title.setStyleSheet(
            "font-size: 18px; font-weight: 700; padding-bottom: 2px;"
        )
        layout.addWidget(title)

        # Custom prompt template
        template_label = QLabel(f"📝 {self.translator.t('prompt_gen.template_label')}")
        template_label.setObjectName("config_label")
        layout.addWidget(template_label)

        self._template_input = QTextEdit()
        self._template_input.setObjectName("config_prompt")
        self._template_input.setPlainText(DEFAULT_TEMPLATE)
        self._template_input.setMaximumHeight(70)
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
        self._idea_input.setMaximumHeight(70)
        layout.addWidget(self._idea_input)

        # AI buttons + Save button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        save_btn = QPushButton(f"💾 {self.translator.t('prompt_gen.save')}")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(36)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f59e0b, stop:1 #d97706);
                color: white; border: none; border-radius: 8px;
                font-size: 13px; font-weight: 700; padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d97706, stop:1 #f59e0b);
            }
            QPushButton:pressed { background: #b45309; }
        """)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        gpt_btn = QPushButton("🤖 ChatGPT")
        gpt_btn.setCursor(Qt.PointingHandCursor)
        gpt_btn.setFixedHeight(36)
        gpt_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10a37f, stop:1 #1a7f64);
                color: white; border: none; border-radius: 8px;
                font-size: 13px; font-weight: 700; padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a7f64, stop:1 #10a37f);
            }
            QPushButton:pressed { background: #0d8c6d; }
        """)
        gpt_btn.clicked.connect(lambda: self._open_ai("chatgpt"))
        btn_row.addWidget(gpt_btn)

        gemini_btn = QPushButton("✨ Gemini")
        gemini_btn.setCursor(Qt.PointingHandCursor)
        gemini_btn.setFixedHeight(36)
        gemini_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4285f4, stop:1 #6d5ce7);
                color: white; border: none; border-radius: 8px;
                font-size: 13px; font-weight: 700; padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d5ce7, stop:1 #4285f4);
            }
            QPushButton:pressed { background: #3b74d4; }
        """)
        gemini_btn.clicked.connect(lambda: self._open_ai("gemini"))
        btn_row.addWidget(gemini_btn)

        layout.addLayout(btn_row)

        # --- Saved Prompts Table ---
        saved_header = QHBoxLayout()
        saved_header.setSpacing(8)

        saved_label = QLabel(f"📋 {self.translator.t('prompt_gen.saved_title')}")
        saved_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        saved_header.addWidget(saved_label, 1)

        del_btn = QPushButton(f"🗑 {self.translator.t('prompt_gen.delete_selected')}")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setFixedHeight(28)
        del_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #EF4444;
                border: 1px solid #FECACA; border-radius: 6px;
                font-size: 12px; padding: 4px 10px;
            }
            QPushButton:hover { background: #FEF2F2; border-color: #F87171; }
        """)
        del_btn.clicked.connect(self._on_delete_selected)
        saved_header.addWidget(del_btn)

        layout.addLayout(saved_header)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels([
            self.translator.t("prompt_gen.col_template"),
            self.translator.t("prompt_gen.col_idea"),
            self.translator.t("prompt_gen.col_date"),
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #374151; border-radius: 8px;
                font-size: 12px; gridline-color: #1f2937;
            }
            QTableWidget::item { padding: 4px 6px; }
            QTableWidget::item:selected { background: #374151; }
            QHeaderView::section {
                background: #1f2937; color: #9CA3AF;
                font-size: 11px; font-weight: 600;
                border: none; padding: 6px 8px;
            }
        """)
        self._table.cellChanged.connect(self._on_cell_edited)
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self._table, 1)

        # Use selected row button
        use_row = QHBoxLayout()
        use_btn = QPushButton(f"⬆️ {self.translator.t('prompt_gen.use_selected')}")
        use_btn.setCursor(Qt.PointingHandCursor)
        use_btn.setFixedHeight(30)
        use_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #8B5CF6;
                border: 1px solid #8B5CF6; border-radius: 6px;
                font-size: 12px; font-weight: 600; padding: 4px 14px;
            }
            QPushButton:hover { background: rgba(139, 92, 246, 0.1); }
        """)
        use_btn.clicked.connect(self._on_use_selected)
        use_row.addStretch()
        use_row.addWidget(use_btn)
        layout.addLayout(use_row)

    # --- Data persistence ---

    def _load_table(self):
        """Load saved prompts into the table."""
        self._prompts = _load_saved_prompts()
        self._refresh_table()

    def _refresh_table(self):
        """Rebuild table rows from self._prompts."""
        self._table.blockSignals(True)
        self._table.setRowCount(len(self._prompts))
        for i, p in enumerate(self._prompts):
            template_item = QTableWidgetItem(p.get("template", ""))
            idea_item = QTableWidgetItem(p.get("idea", ""))
            date_item = QTableWidgetItem(p.get("created_at", ""))
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(i, 0, template_item)
            self._table.setItem(i, 1, idea_item)
            self._table.setItem(i, 2, date_item)
        self._table.blockSignals(False)

    # --- CRUD operations ---

    def _on_save(self):
        """Save current template + idea as a new entry."""
        template = self._template_input.toPlainText().strip()
        idea = self._idea_input.toPlainText().strip()
        if not template and not idea:
            return

        entry = {
            "template": template,
            "idea": idea,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self._prompts.insert(0, entry)
        _save_prompts(self._prompts)
        self._refresh_table()

    def _on_cell_edited(self, row: int, col: int):
        """Update entry when user edits a cell inline."""
        if row < 0 or row >= len(self._prompts):
            return
        item = self._table.item(row, col)
        if not item:
            return
        key = "template" if col == 0 else "idea"
        self._prompts[row][key] = item.text()
        _save_prompts(self._prompts)

    def _on_delete_selected(self):
        """Delete selected rows."""
        rows = sorted(set(idx.row() for idx in self._table.selectedIndexes()), reverse=True)
        if not rows:
            return
        for r in rows:
            if 0 <= r < len(self._prompts):
                self._prompts.pop(r)
        _save_prompts(self._prompts)
        self._refresh_table()

    def _on_use_selected(self):
        """Load selected row's template + idea back into the inputs."""
        rows = set(idx.row() for idx in self._table.selectedIndexes())
        if not rows:
            return
        row = min(rows)
        if 0 <= row < len(self._prompts):
            p = self._prompts[row]
            self._template_input.setPlainText(p.get("template", ""))
            self._idea_input.setPlainText(p.get("idea", ""))

    def _on_row_double_clicked(self, row: int, col: int):
        """Double-click on date column loads the row (non-editable col)."""
        if col == 2:
            self._on_use_selected()

    # --- AI actions ---

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

        clipboard = QApplication.clipboard()
        clipboard.setText(full_text)

        if service == "chatgpt":
            encoded = urllib.parse.quote(full_text, safe="")
            url = f"https://chatgpt.com/?prompt={encoded}"
        else:
            url = "https://gemini.google.com/"

        QDesktopServices.openUrl(QUrl(url))
