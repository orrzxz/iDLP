# iYTDLP — macOS-like GUI for yt-dlp

A modern, macOS-inspired GUI for `yt-dlp` built with PySide6. Supports multiple concurrent downloads, resolution presets, and `cookiesfrombrowser`.

## Quickstart

1. Create/activate venv (already present in this repo):

```bash
source venv/bin/activate
```

2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m app.main
```

## Defaults
- Concurrency: 5
- Default resolution: 720p
- Cookies from browser: None by default (you can choose Safari/Chrome/…)
- Output folder: `~/Movies/iYTDLP`

## Notes
- For high-quality merges, `ffmpeg` is recommended and should be on your PATH.
- Some browsers may need to be closed for `cookiesfrombrowser` to work.
