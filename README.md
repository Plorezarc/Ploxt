# Ploxt Desktop

Ploxt is a simple, modern desktop GUI for downloading video and audio using yt-dlp. It provides a dark-themed interface using CustomTkinter with a custom color theme (colors inspired by Material palettes — this is not a full Material 3 implementation). The app offers an analyze → download workflow, a built-in audio player for playback, and a history of completed downloads.

---

## Highlights
- Dark / Light appearance mode with a custom color theme.
- Analyze a URL, choose a quality or audio-only option, and download in the background.
- Built-in audio playback using pygame.mixer.
- JSON-backed history and user settings.

## Features
- URL analysis (yt-dlp extract_info) and metadata card display
- Background download threads with progress reporting, ETA, and speed
- Audio playback for downloaded audio files
- Persistent download history
- Simple settings screen for output folder, concurrency, and proxy options

## Architecture (brief)
- Entry point: `main.py` — sets up CustomTkinter, applies theme, and launches the AppWindow.
- UI: `ui/` contains the application shell (`app_window.py`), reusable components, and screens (`home_screen.py`, `downloads_screen.py`, `history_screen.py`, `settings_screen.py`).
- Core logic: `core/` contains `downloader.py` (the yt-dlp wrapper and background worker logic), `history.py`, `settings.py`, and `theme.py`.
- Data: `data/` stores JSON assets and local configs.

Design rule: yt-dlp runs in worker threads and never directly touches Tk widgets. Worker threads report back via a thread-safe queue; the main thread polls the queue and updates UI widgets.

## Known issues
- Dark / Light mode: the appearance toggle is currently flaky in some situations — some widgets may not update their colors immediately. A full fix is in progress. Workarounds:
  - Restart the application after changing appearance mode.
  - Manually reopen screens or toggle settings to force a redraw.

- Site extraction: occasionally yt-dlp fails to extract metadata for certain sites. Try updating yt-dlp: `python -m pip install -U yt-dlp`.

## Quick Start (for users)
Requirements:
- Python 3.10 or newer
- ffmpeg installed and available on your PATH (required for merging video/audio streams)

Install and run:
```bash
git clone https://github.com/Plorezarc/Ploxt.git
cd Ploxt
python -m pip install -r requirements.txt
python main.py
```

If you prefer a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate    # Linux / macOS
.venv\Scripts\activate       # Windows
python -m pip install -r requirements.txt
python main.py
```

## Quick Start (for developers)
- Read `core/downloader.py` to understand how downloads and progress hooks are handled.
- UI entry: `ui/app_window.py` builds the navigation and screen routing.
- Add screens by creating `ui/screens/my_screen.py` with a class that extends `ctk.CTkScrollableFrame`, then instantiate it in `AppWindow._build_screens()` and add a nav entry to `NAV_ITEMS` in `app_window.py`.
- To support batch downloads, extend `DownloadManager.start_download()` to accept a list and spawn worker threads up to `settings["concurrent_max"]`.

## File map (top-level)
- `main.py` — application entry point
- `requirements.txt` — Python dependencies
- `core/` — core logic (downloader, theme, history, settings)
- `ui/` — GUI code (app shell, components, screens)
- `data/` — local JSON configuration / assets
- `utils/` — helper utilities

## Development notes
- Dependencies in `requirements.txt` (current highlights):
  - customtkinter
  - yt-dlp
  - Pillow
  - pygame
- The app uses `yt-dlp` as the download engine; keep `yt-dlp` up-to-date if extraction fails for some sites.

## Troubleshooting
- If video downloads fail or audio/video merging fails, verify `ffmpeg` is installed and available in your PATH.
- If a specific site fails to extract, try updating yt-dlp: `python -m pip install -U yt-dlp`
- If the UI freezes, check the console for exceptions from worker threads; long-running actions must not run on the Tk main thread.

## Contributing
Thanks for wanting to contribute! A few suggested starter tasks:
- Add a LICENSE (e.g., MIT) if you want permissive reuse.
- Add screenshots or a short demo GIF to the README for clarity.
- Improve error handling and add unit tests for core modules (history, library helpers).
- Add packaging (PyInstaller) for building standalone executables.

When opening an issue or PR:
- Describe your platform (Windows/macOS/Linux), Python version, and a short reproduction (steps, expected vs actual).
- For PRs: include a short description and test steps; try to keep changes focused and documented.

## Credits & Acknowledgements
- Download backend: yt-dlp — the yt-dlp team
- UI toolkit: CustomTkinter — Tom Schimansky
- Audio playback: Pygame community

## Releases & suggested release notes
Current release tag: v1.0.0-alpha (pre-release). Suggested release body changes:
- Clarify this is an alpha release and list known issues (dark/light toggle, occasional extraction failures).
- Add a downloadable artifact that matches the repository contents (if you include a packaged build).

Suggested short release body:
"Ploxt Alpha v1.0.0 — pre-release\n\nThis is an early alpha release. Known issues: appearance toggle (dark/light) may not update all widgets immediately; some sites may require an updated yt-dlp. Use at your own risk. See README for workarounds and setup instructions."

## License
(No license file found in the repository.) If you want a permissive open-source license, consider adding an `LICENSE` file with the MIT License.
