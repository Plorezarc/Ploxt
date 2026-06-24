# Ploxt Desktop

A clean, modern video and audio downloader powered by https://github.com/yt-dlp/yt-dlp and built with Python + CustomTkinter. 

---

## Features & UI Elements

Ploxt Desktop focuses on a dark, responsive interface designed for quick and efficient media fetching:
- **Dark & Light Modes:** Built using custom color palettes (`#121318` dark surface).(Still Fixing)
- **Navigation Rail:** Quick desktop routing to easily swap between active screens.
- **Built-in Player:** Seamlessly integrated with `pygame.mixer` to play downloaded audio directly inside the app.

---

## Architecture

```text
ploxt_desktop/
├── main.py              # Entry point — Tk root + AppWindow
│
├── core/
│   ├── theme.py         # Theme tokens & ThemeManager
│   ├── downloader.py    # yt-dlp wrapper (threaded, progress hooks)
│   ├── history.py       # JSON-backed download history
│   └── settings.py      # User settings persistence
│
├── ui/
│   ├── app_window.py    # Root shell: NavRail + screen routing
│   ├── components/
│   │   └── m3_widgets.py # Custom UI cards, buttons, nav rail widgets...
│   └── screens/
│       ├── home_screen.py      # URL input → Analyze → Info Card → Download
│       ├── downloads_screen.py # Active downloads list
│       ├── history_screen.py   # Completed downloads log
│       └── settings_screen.py  # Folder, proxy, configurations, about
│
├── utils/               # Platform and internal utilities
├── data/                # Local JSON assets and configuration storage
└── requirements.txt
Main Thread (Tk event loop)
    │
    │  root.after(80ms) ──► DownloadManager._poll()
    │                                │
    │                                │  queue.Queue (thread-safe)
    │                                │      ▲
    │                         drain & dispatch
    │                                │
    └──── UI callbacks (handle_event) ◄──┘
                                         ▲
                                    Worker threads
                                    ┌──────────────────┐
                                    │ _extract_worker  │  → "info" / "error"
                                    │ _download_worker │  → "progress" / "finished" / "error"
                                   └──────────────────┘
**Rule**: yt-dlp _never_ touches Tkinter widgets directly. All updates flow through `queue.Queue` → `root.after()` → callbacks on the main thread.
```
---

## Quick Start ( For Developer )

### 1. Prerequisites

- Python 3.10+
- `ffmpeg` in your PATH (required for merging video+audio streams)

### 2. Install

```bash
git clone [https://github.com/plorezarc/ploxt-desktop]
cd ploxt-desktop
pip install -r requirements.txt
python main.py

# User Flow

[ Paste URL ] ──► [ Analyze ]
                       │
                  (background thread: yt-dlp extract_info)
                       │
               ◄── [ Video Info Card appears ]
                       │
                  Select quality from dropdown
                  Choose output folder
                       │
               [ Download ] or [ Audio Only ]
                       │
                  (background thread: yt-dlp download)
                       │  ── progress_hook ──► queue ──► UI poll
                       │
               ◄── Progress bar + speed + ETA update
                       │
               <-- [ Download complete ]
                       │
                  Saved to History
Extending
Add a new screen
Create ui/screens/my_screen.py with a class extending ctk.CTkScrollableFrame
```
Instantiate it in AppWindow._build_screens()

Add a nav entry to NAV_ITEMS in app_window.py
Batch downloads
Extend DownloadManager.start_download() to accept a list; spawn one thread per item up to settings["concurrent_max"].

Credits
Original core concepts adapted from JunkFood02's layout architecture

yt-dlp — yt-dlp team (download engine)

CustomTkinter — Tom Schimansky (modern Tk widgets)

Pygame — Pygame community (audio mixer backend)
