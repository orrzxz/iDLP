from __future__ import annotations

from typing import Dict

# Maps UI labels to yt-dlp format strings
_FORMATS: Dict[str, str] = {
    "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "Audio only": "bestaudio/best",
}


def format_for_label(label: str) -> str:
    return _FORMATS.get(label, _FORMATS["720p"])  # default to 720p
