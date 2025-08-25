from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QGuiApplication
from PySide6.QtWidgets import QApplication, QStyleFactory

from app.ui.main_window import MainWindow


def apply_macos_like_theme(app: QApplication) -> None:
    # Prefer macOS native, else Fusion. Apply a dark palette and a light stylesheet polish.
    available = QStyleFactory.keys()
    use_macos = "macOS" in available
    app.setStyle("macOS" if use_macos else "Fusion")

    # Dark palette (macOS-like)
    palette = QPalette()
    window = QColor(28, 28, 30)      # #1C1C1E
    base = QColor(22, 22, 24)        # #161618
    alt = QColor(36, 36, 38)         # #242426
    text = QColor(230, 230, 235)
    disabled_text = QColor(150, 150, 155)
    button = QColor(44, 44, 46)      # #2C2C2E
    highlight = QColor(10, 132, 255) # macOS system blue

    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, alt)
    palette.setColor(QPalette.ToolTipBase, window)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Button, button)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
    palette.setColor(QPalette.BrightText, QColor(255, 85, 85))
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)

    # Minimal stylesheet polish (names used by MainWindow: Card, CardTitle, Chip, PrimaryButton)
    app.setStyleSheet(
        """
        QMainWindow, QWidget { color: #E6E6EB; }

        QFrame#Card {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
        }
        QLabel#CardTitle {
            font-size: 15px;
            font-weight: 600;
            color: #FFFFFF;
        }
        QLabel#Chip {
            background: rgba(255,255,255,0.10);
            border-radius: 8px;
            padding: 2px 8px;
            color: #FFFFFF;
        }
        QPushButton#PrimaryButton {
            background: #0A84FF;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            font-weight: 600;
        }
        QPushButton#PrimaryButton:hover { background: #2A95FF; }
        QPushButton#PrimaryButton:pressed { background: #0067D1; }
        QPushButton#PrimaryButton:disabled { background: #3A3A3C; color: #9A9AA0; }

        QToolButton { padding: 4px 8px; border-radius: 8px; }
        QToolButton:hover { background: rgba(255,255,255,0.08); }
        QToolButton:pressed { background: rgba(255,255,255,0.12); }

        QLineEdit, QComboBox {
            padding: 6px 8px;
            border-radius: 8px;
            background: rgba(118,118,128,0.24);
            border: 1px solid rgba(255,255,255,0.10);
            selection-background-color: #0A84FF;
            selection-color: white;
        }
        QComboBox QAbstractItemView {
            background: #2C2C2E;
            color: #E6E6EB;
            selection-background-color: #0A84FF;
            selection-color: white;
            border: 1px solid rgba(255,255,255,0.12);
        }

        QTableView {
            background: transparent;
            alternate-background-color: rgba(255,255,255,0.04);
            gridline-color: rgba(255,255,255,0.10);
            selection-background-color: rgba(10,132,255,0.28);
            selection-color: white;
        }
        QHeaderView::section {
            background: rgba(255,255,255,0.08);
            color: #E6E6EB;
            padding: 6px;
            border: none;
            border-right: 1px solid rgba(255,255,255,0.10);
        }
        QStatusBar {
            background: rgba(255,255,255,0.04);
            border-top: 1px solid rgba(255,255,255,0.08);
        }
        """
    )


def main() -> int:
    # Qt6 enables high-DPI scaling by default; no need to set deprecated attributes.
    app = QApplication(sys.argv)
    app.setOrganizationName("com.yourname")
    app.setOrganizationDomain("com.yourname.iytdlp")
    app.setApplicationName("iYTDLP")

    apply_macos_like_theme(app)

    win = MainWindow()
    win.resize(1000, 640)
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
