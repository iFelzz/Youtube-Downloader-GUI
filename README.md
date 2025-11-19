# Youtube-Downloader-GUI

Simple GUI wrapper around `yt-dlp` for downloading YouTube audio/video.

## Requirements

- Python 3.8+
- `yt-dlp` available on PATH (see installation below)

Optional: run in a virtual environment.

## Installing yt-dlp (Windows)

1. Open PowerShell as Administrator (optional).
2. Install via pip:

```powershell
python -m pip install --upgrade yt-dlp
```

3. Verify installation:

```powershell
yt-dlp --version
```

## Usage

1. Run the app:

```powershell
python .\main.py
```

2. Paste a YouTube URL, choose mode MP3 or MP4, choose folder output.
3. For MP4: click mode MP4, choose resolution from list, and click `Download`.

## Logging

App writes logs to `ytdl_gui.log` in the working directory for troubleshooting.

## Notes

- This GUI calls the `yt-dlp` executable; make sure it is on PATH.
- On Windows filenames may be sanitized by `yt-dlp`.

Contributions and issues are welcome.
