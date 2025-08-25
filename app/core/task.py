from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import QObject, QRunnable, Signal

from app.core.formats import format_for_label
from app.core.utils import browser_key_from_label, detect_ffmpeg


class TaskSignals(QObject):
    progress = Signal(int, dict)  # row, progress dict from yt-dlp
    status = Signal(int, str)     # row, status text
    finished = Signal(int, dict)  # row, result info
    failed = Signal(int, str)     # row, error text


class DownloadTask(QRunnable):
    def __init__(
        self,
        row: int,
        url: str,
        outdir: Path,
        resolution_label: str,
        cookies_label: Optional[str],
        selected_format: Optional[str] = None,
        embed_thumbnail: bool = False,
        add_metadata: bool = False,
    ) -> None:
        super().__init__()
        self.row = row
        self.url = url
        self.outdir = outdir
        self.resolution_label = resolution_label
        self.cookies_label = cookies_label
        self.selected_format = (selected_format or "Auto").strip()
        self.embed_thumbnail = embed_thumbnail
        self.add_metadata = add_metadata
        self.signals = TaskSignals()
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()

    def run(self) -> None:
        # Import yt_dlp lazily inside thread to avoid UI startup penalty
        try:
            import yt_dlp as ytdlp  # type: ignore
        except Exception as e:  # pragma: no cover
            self.signals.failed.emit(self.row, f"yt-dlp import error: {e}")
            return

        fmt = format_for_label(self.resolution_label)

        def hook(d: dict) -> None:
            # Emit progress updates to UI
            self.signals.progress.emit(self.row, d)
            if self._cancelled.is_set():
                raise KeyboardInterrupt("Cancelled")

        ydl_opts: dict = {
            "outtmpl": str(self.outdir / "%(title)s [%(id)s].%(ext)s"),
            "format": fmt,
            "noprogress": True,
            "quiet": True,
            "progress_hooks": [hook],
        }

        # Apply container/format preferences
        sf = (self.selected_format or "").upper()
        postprocessors: List[dict] = []
        has_ffmpeg = detect_ffmpeg()

        if sf == "MP3":
            # Force audio-only; extract to mp3 only if ffmpeg is available
            ydl_opts["format"] = "bestaudio/best"
            if has_ffmpeg:
                postprocessors.append({
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                })
                if self.embed_thumbnail:
                    postprocessors.append({"key": "EmbedThumbnail"})
                if self.add_metadata:
                    postprocessors.append({"key": "FFmpegMetadata"})
        else:
            if sf == "MP4":
                ydl_opts["merge_output_format"] = "mp4"
            elif sf == "WEBM":
                ydl_opts["merge_output_format"] = "webm"
            # Optional postprocessors for video outputs
            if self.add_metadata and has_ffmpeg:
                postprocessors.append({"key": "FFmpegMetadata"})
            if self.embed_thumbnail and has_ffmpeg:
                postprocessors.append({"key": "EmbedThumbnail"})

        if postprocessors:
            ydl_opts["postprocessors"] = postprocessors

        browser_key = browser_key_from_label(self.cookies_label or "")
        if browser_key:
            # yt-dlp expects a tuple; profile/keyring left default
            ydl_opts["cookiesfrombrowser"] = (browser_key,)

        try:
            self.signals.status.emit(self.row, "Starting…")
            with ytdlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.signals.finished.emit(self.row, {"url": self.url})
        except KeyboardInterrupt:
            self.signals.status.emit(self.row, "Cancelled")
            self.signals.failed.emit(self.row, "Cancelled")
        except Exception as e:
            self.signals.status.emit(self.row, "Error")
            self.signals.failed.emit(self.row, str(e))
