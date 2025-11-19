# YouTube Downloader GUI

Simple cross-platform GUI wrapper for downloading YouTube audio/video using yt-dlp.

This project provides a small Tkinter GUI that prefers the `yt_dlp` Python API when available
and falls back to the `yt-dlp` executable if needed. The app supports audio extraction (MP3),
video downloads (MP4) with selectable resolution, and shows a download popup with percentage
and transfer speed.

---

## Requirements

- Python 3.8 or newer (for development / running from source).
- Optional but recommended: `yt-dlp` Python package (`pip install yt-dlp`).
- `ffmpeg` is required for audio extraction (MP3). The build/instructions below show how to
  bundle ffmpeg with the application so end users don't need to install it system-wide.

## Running from source

1. (Recommended) Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install --upgrade pip
pip install yt-dlp
```

2. Run the GUI:

```powershell
python .\\main.py
```

3. Paste a YouTube URL, pick `MP3` or `MP4`, choose an output folder. For MP4, select a
   resolution and click `Download`.

Logs are written to `ytdl_gui.log` in the working directory for troubleshooting.

---

## Building an executable (Windows)

This project includes `build.ps1`, a helper script that runs PyInstaller and will include
any `ffmpeg.exe` or `yt-dlp.exe` placed under the `packages/` folder.

Recommended workflow (PowerShell):

```powershell
# from project root
.\\build.ps1        # produces a one-folder build under dist\\YouTubeDownloader
# or for a single-file executable
.\\build.ps1 -OneFile
```

How it works:
- `build.ps1` searches `./packages` for `ffmpeg.exe` and `yt-dlp.exe` and passes them to
  PyInstaller as additional binaries so the produced bundle contains these tools.
- The app contains logic (`find_ffmpeg()`) to locate a bundled `ffmpeg` (in the extracted
  PyInstaller _MEIPASS folder, in `./ffmpeg/`, or via `YTDL_FFMPEG` environment variable).

### Portable vs Installer

- Portable (recommended for simple distribution): use the one-folder output `dist\\YouTubeDownloader\\`. Zip
  that folder and distribute — users extract and run `YouTubeDownloader.exe`.
- Installer (recommended for non-technical users): use the Inno Setup script at
  `installer\\YouTubeDownloader.iss` to create a Windows installer (Next→Next→Finish) that copies
  files to Program Files and creates shortcuts.

To build the installer:

1. Build the application with `build.ps1` (one-folder mode).
2. Open `installer\\YouTubeDownloader.iss` in Inno Setup Compiler and compile it.

The Inno Setup script included will:
- Copy the entire `dist\\YouTubeDownloader\\` folder into the Program Files install directory.
- Display the `LICENSE` file during install.
- Create a Start Menu shortcut and (optionally) a Desktop shortcut.

---

## Bundling notes & troubleshooting

- If you bundle ffmpeg with PyInstaller, the application will find it automatically. If you
  place ffmpeg somewhere else, set the environment variable `YTDL_FFMPEG` to the ffmpeg
  executable path to override detection.
- If you rely on the `yt-dlp` executable instead of the Python package, put `yt-dlp.exe`
  into `packages/` so `build.ps1` can include it.
- If the produced executable fails to run on another PC, run it from `cmd.exe` to capture
  stdout/stderr, or check `ytdl_gui.log` in the working directory for stack traces.

---

## License

See the `LICENSE` file in the project root.

---

If you want, I can:
- Add an automated `release.ps1` that zips the `dist` folder and prepares an artifacts directory,
- Add an installer option in the Inno Setup script to let the user choose whether to install a
  desktop shortcut (checkbox), or
- Help you customize a small icon (`.ico`) to be used for the installer and shortcuts.

Choose what to add next and I will implement it.
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
