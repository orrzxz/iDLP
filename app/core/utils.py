from __future__ import annotations

import re
import shutil
from typing import Optional

import humanize

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def is_valid_url(s: str) -> bool:
    return bool(_URL_RE.match(s.strip()))


def human_bytes(n: Optional[float]) -> str:
    if not n:
        return "-"
    return humanize.naturalsize(n, binary=False, format="%.1f")


def human_rate(n: Optional[float]) -> str:
    if not n:
        return "-"
    return f"{humanize.naturalsize(n, binary=False, format='%.1f')}/s"


def human_eta(seconds: Optional[float]) -> str:
    if not seconds:
        return "-"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def detect_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def browser_key_from_label(label: str) -> Optional[str]:
    label = (label or "").strip()
    if not label or label.lower() == "none":
        return None
    mapping = {
        "safari": "safari",
        "chrome": "chrome",
        "chromium": "chromium",
        "brave": "brave",
        "edge": "edge",
        "firefox": "firefox",
    }
    return mapping.get(label.lower())
