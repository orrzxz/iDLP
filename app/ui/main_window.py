from __future__ import annotations

from pathlib import Path

from typing import Dict

from PySide6.QtCore import Qt, QThreadPool, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolButton,
    QMenu,
    QTableView,
    QToolBar,
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar,
    QFrame,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from PySide6.QtWidgets import QStyle, QGraphicsDropShadowEffect
import sys

from app.ui.add_links_dialog import AddLinksDialog
from app.ui.preferences_dialog import PreferencesDialog
from app.core.task import DownloadTask
from app.core.utils import is_valid_url, human_bytes, human_rate, human_eta


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("iYTDLP")
        self.setUnifiedTitleAndToolBarOnMac(True)

        self._output_dir = Path.home() / "Movies" / "iYTDLP"
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Concurrency
        self.threadpool = QThreadPool.globalInstance()
        self.threadpool.setMaxThreadCount(5)  # default concurrency

        # Task registry: row -> task
        self._tasks: Dict[int, DownloadTask] = {}

        self._build_toolbar()
        self._build_table()
        self._build_menubar()
        self._build_statusbar()

    # UI builders
    def _build_toolbar(self) -> None:
        tb = QToolBar("Main Toolbar", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.TopToolBarArea, tb)

        # Add Links action
        self.action_add = QAction(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), "Add Links…", self)
        # mac-like shortcut uses Command (Meta) on macOS
        self.action_add.setShortcut("Meta+L" if sys.platform == "darwin" else "Ctrl+L")
        self.action_add.triggered.connect(self.on_add_links)
        tb.addAction(self.action_add)

        # Output directory picker
        self.action_output = QAction(self.style().standardIcon(QStyle.SP_DirIcon), "Output Folder", self)
        self.action_output.triggered.connect(self.on_pick_output)
        tb.addAction(self.action_output)

        tb.addSeparator()

        # Resolution combo
        self.res_combo = QComboBox(self)
        self.res_combo.addItems([
            "2160p","1440p","1080p","720p","480p","360p","Audio only"
        ])
        self.res_combo.setCurrentText("720p")  # default as requested
        tb.addWidget(self.res_combo)

        # Cookies browser combo
        self.cookies_combo = QComboBox(self)
        self.cookies_combo.addItems([
            "None", "Safari", "Chrome", "Chromium", "Brave", "Edge", "Firefox"
        ])
        self.cookies_combo.setCurrentText("None")  # default none
        tb.addWidget(self.cookies_combo)

        tb.addSeparator()

        # Start/Stop all
        self.action_start_all = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), "Start All", self)
        self.action_stop_all = QAction(self.style().standardIcon(QStyle.SP_MediaStop), "Stop All", self)
        self.action_start_all.triggered.connect(self.on_start_all)
        self.action_stop_all.triggered.connect(self.on_stop_all)
        tb.addAction(self.action_start_all)
        tb.addAction(self.action_stop_all)

    def _build_table(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

        # Top card
        self._build_top_card(layout)

        # Section title
        title = QLabel("Download History", self)
        layout.addWidget(title)

        self.table = QTableView(self)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSortingEnabled(False)
        self.table.setShowGrid(False)
        vh = self.table.verticalHeader()
        vh.setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setStretchLastSection(True)

        self.model = QStandardItemModel(0, 8, self)
        self.model.setHorizontalHeaderLabels([
            "Title/URL", "Progress", "Speed", "ETA", "Size", "Status", "Resolution", "Output"
        ])
        self.table.setModel(self.model)

        # Column sizing for readability on macOS
        try:
            from PySide6.QtWidgets import QHeaderView
            hh.setSectionResizeMode(0, QHeaderView.Stretch)
            hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
            hh.setSectionResizeMode(7, QHeaderView.Stretch)
        except Exception:
            pass

        layout.addWidget(self.table)
        self.setCentralWidget(central)

    def _build_top_card(self, parent_layout: QVBoxLayout) -> None:
        card = QFrame(self)
        card.setObjectName("Card")
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        title = QLabel("Download Video", card)
        title.setObjectName("CardTitle")
        v.addWidget(title)

        self.url_edit = QLineEdit(card)
        self.url_edit.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_edit.setClearButtonEnabled(True)
        v.addWidget(self.url_edit)

        controls = QHBoxLayout()

        # Format button with menu (placeholder options)
        self.selected_format = "Auto"
        self.btn_format = QToolButton(card)
        self.btn_format.setText("Format: Auto")
        self.btn_format.setPopupMode(QToolButton.InstantPopup)
        self.menu_format = QMenu(self.btn_format)
        for fmt in ("Auto", "MP4", "WebM", "MP3"):
            act = self.menu_format.addAction(fmt)
            act.setCheckable(True)
            act.setChecked(fmt == self.selected_format)
            act.triggered.connect(lambda _=False, f=fmt: self._on_format_selected(f))
        self.btn_format.setMenu(self.menu_format)
        controls.addWidget(self.btn_format)

        # Quality chooser mirrors toolbar resolution combo
        self.quality_combo = QComboBox(card)
        self.quality_combo.addItems(["2160p","1440p","1080p","720p","480p","360p","Audio only"])
        self.quality_combo.setCurrentText("720p")
        self.quality_combo.currentTextChanged.connect(self._on_quality_changed)
        controls.addWidget(self.quality_combo)

        # Advanced menu with toggles
        self.adv_embed_thumb = False
        self.adv_add_metadata = False
        self.btn_adv = QToolButton(card)
        self.btn_adv.setText("Advanced")
        self.btn_adv.setPopupMode(QToolButton.InstantPopup)
        self.menu_adv = QMenu(self.btn_adv)
        self.act_adv_thumb = self.menu_adv.addAction("Embed thumbnail")
        self.act_adv_thumb.setCheckable(True)
        self.act_adv_thumb.toggled.connect(self._on_adv_toggle_embed)
        self.act_adv_meta = self.menu_adv.addAction("Add metadata")
        self.act_adv_meta.setCheckable(True)
        self.act_adv_meta.toggled.connect(self._on_adv_toggle_metadata)
        self.btn_adv.setMenu(self.menu_adv)
        controls.addStretch(1)
        controls.addWidget(self.btn_adv)

        # Download button
        self.btn_download = QPushButton("Download", card)
        self.btn_download.setObjectName("PrimaryButton")
        self.btn_download.clicked.connect(self.on_download_click)
        controls.addWidget(self.btn_download)

        v.addLayout(controls)

        # Chips row
        chips = QHBoxLayout()
        self.chip_format = QLabel("Auto", card)
        self.chip_format.setObjectName("Chip")
        self.chip_quality = QLabel("720p", card)
        self.chip_quality.setObjectName("Chip")
        self.chip_meta = QLabel("Metadata", card)
        self.chip_meta.setObjectName("Chip")
        self.chip_meta.setVisible(False)
        self.chip_thumb = QLabel("Thumbnail", card)
        self.chip_thumb.setObjectName("Chip")
        self.chip_thumb.setVisible(False)
        chips.addWidget(self.chip_format)
        chips.addWidget(self.chip_quality)
        chips.addWidget(self.chip_meta)
        chips.addWidget(self.chip_thumb)
        chips.addStretch(1)
        v.addLayout(chips)

        # Inline progress placeholder
        self.inline_progress = QProgressBar(card)
        self.inline_progress.setTextVisible(False)
        self.inline_progress.setMaximum(100)
        self.inline_progress.setValue(0)
        v.addWidget(self.inline_progress)

        # Soft shadow for the card
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 160))
        card.setGraphicsEffect(shadow)

        parent_layout.addWidget(card)

    def _build_menubar(self) -> None:
        mb = self.menuBar()
        app_menu = mb.addMenu("iYTDLP")

        # About
        self.action_about = QAction("About iYTDLP", self)
        self.action_about.setMenuRole(QAction.MenuRole.AboutRole)
        self.action_about.triggered.connect(self.on_about)
        app_menu.addAction(self.action_about)

        # Preferences
        self.action_prefs = QAction("Preferences…", self)
        self.action_prefs.setShortcut("Meta+," if sys.platform == "darwin" else "Ctrl+,")
        self.action_prefs.setMenuRole(QAction.MenuRole.PreferencesRole)
        self.action_prefs.triggered.connect(self.on_preferences)
        app_menu.addAction(self.action_prefs)

        app_menu.addSeparator()

        # Quit
        self.action_quit = QAction("Quit iYTDLP", self)
        self.action_quit.setShortcut("Meta+Q" if sys.platform == "darwin" else "Ctrl+Q")
        self.action_quit.setMenuRole(QAction.MenuRole.QuitRole)
        self.action_quit.triggered.connect(QApplication.instance().quit)
        app_menu.addAction(self.action_quit)

    def _build_statusbar(self) -> None:
        sb = self.statusBar()
        sb.setSizeGripEnabled(False)
        self._lbl_queued = QLabel("Queued: 0", self)
        self._lbl_active = QLabel("Active: 0", self)
        self._lbl_completed = QLabel("Completed: 0", self)
        self._lbl_errors = QLabel("Errors: 0", self)
        for w in (self._lbl_queued, self._lbl_active, self._lbl_completed, self._lbl_errors):
            sb.addPermanentWidget(w)
        self._update_counts()

    # Slots
    def on_add_links(self) -> None:
        dlg = AddLinksDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        urls = [u for u in dlg.get_urls() if is_valid_url(u)]
        if not urls:
            self.statusBar().showMessage("No valid URLs provided", 3000)
            return
        for url in urls:
            self._append_task_row(url)
        self.statusBar().showMessage(f"Queued {len(urls)} URL(s)", 2000)

    def on_pick_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Choose Output Folder", str(self._output_dir)
        )
        if directory:
            self._output_dir = Path(directory)
            self.statusBar().showMessage(f"Output: {self._output_dir}", 2000)

    def on_start_all(self) -> None:
        # Start or restart queued tasks
        rows = self.model.rowCount()
        for row in range(rows):
            self._start_row(row)

    def on_stop_all(self) -> None:
        for row, task in list(self._tasks.items()):
            task.cancel()
            self._on_task_status(row, "Cancelling…")

    # Helpers
    def _append_task_row(self, url: str) -> None:
        row = self.model.rowCount()
        self.model.insertRow(row)
        out = str(self._output_dir)
        resolution = self.res_combo.currentText()
        values = [
            url,
            "0%",
            "-",
            "-",
            "-",
            "Queued",
            resolution,
            out,
        ]
        for col, val in enumerate(values):
            item = QStandardItem(val)
            if col != 0:
                item.setEditable(False)
            self.model.setItem(row, col, item)
        self._update_counts()

    def _start_row(self, row: int) -> None:
        status_item = self.model.item(row, 5)
        status = status_item.text() if status_item else ""
        if status in ("Completed", "Downloading", "Starting…"):
            return
        url = self.model.item(row, 0).text()
        resolution = self.model.item(row, 6).text()
        cookies_label = self.cookies_combo.currentText()
        task = DownloadTask(
            row, url, self._output_dir, resolution, cookies_label,
            self.selected_format, self.adv_embed_thumb, self.adv_add_metadata
        )
        task.signals.progress.connect(self._on_task_progress)
        task.signals.status.connect(self._on_task_status)
        task.signals.finished.connect(self._on_task_finished)
        task.signals.failed.connect(self._on_task_failed)
        self._tasks[row] = task
        self._on_task_status(row, "Starting…")
        self.threadpool.start(task)

    def _on_adv_toggle_embed(self, checked: bool) -> None:
        self.adv_embed_thumb = checked
        self.chip_thumb.setVisible(checked)

    def _on_adv_toggle_metadata(self, checked: bool) -> None:
        self.adv_add_metadata = checked
        self.chip_meta.setVisible(checked)

    # Top card handlers
    def _on_quality_changed(self, text: str) -> None:
        # Keep toolbar combo in sync for model entries
        self.res_combo.setCurrentText(text)
        self.chip_quality.setText(text)

    def _on_format_selected(self, fmt: str) -> None:
        self.selected_format = fmt
        # Update checks
        for act in self.menu_format.actions():
            act.setChecked(act.text() == fmt)
        self.chip_format.setText(fmt)
        self.btn_format.setText(f"Format: {fmt}")
        # If MP3 selected, force Audio only quality
        if fmt.upper().startswith("MP3"):
            self.quality_combo.setCurrentText("Audio only")

    def on_download_click(self) -> None:
        url = (self.url_edit.text() or "").strip()
        if not is_valid_url(url):
            self.statusBar().showMessage("Please enter a valid URL", 2000)
            return
        # Ensure model uses current quality selection
        self.res_combo.setCurrentText(self.quality_combo.currentText())
        self._append_task_row(url)
        self.url_edit.clear()
        # Start the last row only
        self._start_row(self.model.rowCount() - 1)

    # Signal handlers
    def _on_task_progress(self, row: int, d: dict) -> None:
        if row >= self.model.rowCount():
            return
        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes") or 0
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            percent = int(downloaded * 100 / total) if total else 0
            speed = d.get("speed")
            eta = d.get("eta")
            self.model.item(row, 1).setText(f"{percent}%")
            self.model.item(row, 2).setText(human_rate(speed))
            self.model.item(row, 3).setText(human_eta(eta))
            self.model.item(row, 4).setText(human_bytes(total))
            self.model.item(row, 5).setText("Downloading")
            # Reflect progress on top card for the latest queued row
            if row == self.model.rowCount() - 1:
                self.inline_progress.setValue(percent)

    def _on_task_status(self, row: int, text: str) -> None:
        if row < self.model.rowCount():
            self.model.item(row, 5).setText(text)
            self._update_counts()

    def _on_task_finished(self, row: int, result: dict) -> None:
        if row < self.model.rowCount():
            self.model.item(row, 1).setText("100%")
            self.model.item(row, 5).setText("Completed")
            self._update_counts()

    def _on_task_failed(self, row: int, error: str) -> None:
        if row < self.model.rowCount():
            self.model.item(row, 5).setText(f"Error: {error}")
            self._update_counts()

    # Menu handlers
    def on_about(self) -> None:
        QMessageBox.about(
            self,
            "About iYTDLP",
            "<b>iYTDLP</b><br>Simple, macOS-friendly UI for yt-dlp downloads.",
        )

    def on_preferences(self) -> None:
        dlg = PreferencesDialog(self.threadpool.maxThreadCount(), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            maxc = dlg.get_max_concurrency()
            self.threadpool.setMaxThreadCount(maxc)
            self.statusBar().showMessage(f"Max concurrency set to {maxc}", 2000)
            self._update_counts()

    # Counters
    def _update_counts(self) -> None:
        rows = self.model.rowCount()
        queued = active = completed = errors = 0
        for r in range(rows):
            status_item = self.model.item(r, 5)
            st = status_item.text() if status_item else ""
            if st.startswith("Error"):
                errors += 1
            elif st == "Completed":
                completed += 1
            elif st in ("Starting…", "Downloading", "Cancelling…"):
                active += 1
            elif st == "Queued":
                queued += 1
        self._lbl_queued.setText(f"Queued: {queued}")
        self._lbl_active.setText(f"Active: {active}")
        self._lbl_completed.setText(f"Completed: {completed}")
        self._lbl_errors.setText(f"Errors: {errors}")
