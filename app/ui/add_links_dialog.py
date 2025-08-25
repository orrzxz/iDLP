from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtGui import QGuiApplication


class AddLinksDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Links")
        self.resize(560, 320)

        layout = QVBoxLayout(self)

        self.text = QTextEdit(self)
        self.text.setPlaceholderText("Paste one URL per line…")
        layout.addWidget(self.text)

        # Buttons row with Paste from Clipboard convenience
        row = QHBoxLayout()
        self.paste_btn = QPushButton("Paste from Clipboard", self)
        self.paste_btn.clicked.connect(self._paste)
        row.addWidget(self.paste_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _paste(self) -> None:
        cb = QGuiApplication.clipboard()
        self.text.insertPlainText(cb.text())

    def get_urls(self) -> List[str]:
        raw = self.text.toPlainText().splitlines()
        urls = [line.strip() for line in raw if line.strip()]
        return urls
