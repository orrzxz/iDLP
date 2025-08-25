from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
)


class PreferencesDialog(QDialog):
    """
    Minimal Preferences dialog stub.
    Currently allows setting max concurrent downloads.
    """

    def __init__(self, current_concurrency: int = 5, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(400, 140)

        layout = QFormLayout(self)

        self.spin_concurrency = QSpinBox(self)
        self.spin_concurrency.setRange(1, 32)
        self.spin_concurrency.setValue(int(current_concurrency) if current_concurrency else 5)
        layout.addRow("Max concurrent downloads:", self.spin_concurrency)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_max_concurrency(self) -> int:
        return int(self.spin_concurrency.value())
