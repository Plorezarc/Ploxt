"""
ui/app_window.py
─────────────────────────────────────────────────────────────────────────────
Root application shell.

Layout
──────
┌──────────────────────────────────────────────────────────────────────┐
│  NavRail (88 px)  │  Content Area (fills remaining width)            │
│                   │                                                   │
│   Ploxt           │  <active screen>                                  │
│                   │                                                   │
│   H   Home        │                                                   │
│   D   Downloads   │                                                   │
│   R   History     │                                                   │
│   S   Settings    │                                                   │
│                   │                                                   │
│   ☀/🌙 (theme)   │                                                   │
└──────────────────────────────────────────────────────────────────────┘

Screens are all constructed once and swapped in/out with pack/forget
so their state is preserved when navigating.

Event routing
─────────────
The DownloadManager posts events to _on_dl_event() which:
  • forwards "info" / "progress" / "finished" / "error" to HomeScreen
  • also updates DownloadsScreen progress rows
  • records finished downloads in HistoryScreen
"""

from __future__ import annotations
from pathlib import Path
import customtkinter as ctk

from core.theme import ThemeManager, TypeScale, Shape
from core.downloader import DownloadManager
from core.history import HistoryManager
from core.settings import AppSettings
from core.library import scan_audio_files

from ui.screens.home_screen import HomeScreen
from ui.screens.downloads_screen import DownloadsScreen
from ui.screens.history_screen import HistoryScreen
from ui.screens.settings_screen import SettingsScreen
from ui.components.m3_widgets import M3NavRail


NAV_ITEMS = [
    ("Home",      "H"),
    ("Downloads", "D"),
    ("History",   "R"),
    ("Settings",  "S"),
]


class AppWindow(ctk.CTkFrame):
    """Top-level frame — the entire visible surface of the application."""

    def __init__(self, root: ctk.CTk, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("fg_color", s.surface)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(root, **kwargs)

        self._win     = root   # renamed: avoid collision with Tkinter's _root() method
        self._current = 0   # active nav index
        self._dl_idx  = -1  # current download entry in DownloadsScreen

        # ── Shared services ──────────────────────────────────────────────────
        self._settings = AppSettings()
        self._hist_mgr = HistoryManager()
        self._dl_mgr   = DownloadManager(
            event_callback=self._on_dl_event,
            root=root,
            proxy=self._settings.get("proxy") or None,
        )

        # ── Build layout ─────────────────────────────────────────────────────
        self._build_layout()
        self._build_screens()
        self._show_screen(0)
        self._refresh_library_summary()

    # ═════════════════════════════ LAYOUT ════════════════════════════════════

    def _build_layout(self) -> None:
        s = ThemeManager.scheme
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ── Left navigation rail ─────────────────────────────────────────────
        self._nav_rail = M3NavRail(
            self,
            items=NAV_ITEMS,
            on_change=self._show_screen,
            on_library_click=lambda: self._show_screen(1),
        )
        self._nav_rail.grid(row=0, column=0, sticky="ns")

        # ── Content container ────────────────────────────────────────────────
        self._content = ctk.CTkFrame(
            self,
            fg_color=s.surface,
            corner_radius=0,
        )
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.rowconfigure(0, weight=1)
        self._content.columnconfigure(0, weight=1)

    # ═════════════════════════════ SCREENS ════════════════════════════════════

    def _build_screens(self) -> None:
        """Construct all screens once; they share the same parent container."""
        self._screens: list[ctk.CTkBaseClass] = []

        # 0 — Home
        home = HomeScreen(
            self._content,
            download_mgr=self._dl_mgr,
            history_mgr=self._hist_mgr,
            settings=self._settings,
            on_download_start=self._on_download_started,
        )
        self._screens.append(home)
        self._home_screen = home

        # 1 — Downloads
        downloads = DownloadsScreen(self._content, settings=self._settings)
        self._screens.append(downloads)
        self._dl_screen = downloads

        # 2 — History
        history = HistoryScreen(self._content, history_mgr=self._hist_mgr)
        self._screens.append(history)
        self._hist_screen = history

        # 3 — Settings
        settings = SettingsScreen(
            self._content,
            settings=self._settings,
            root=self._win,
        )
        self._screens.append(settings)

    def _show_screen(self, index: int) -> None:
        """Swap visible screen; preserve states."""
        if index == self._current and self._screens[index].winfo_ismapped():
            if index == 1:
                self._dl_screen.refresh_files()
                self._refresh_library_summary()
            if index == 2:
                self._hist_screen.refresh()
            return   # already visible

        # Hide all
        for sc in self._screens:
            sc.grid_forget()

        # Show requested
        self._screens[index].grid(row=0, column=0, sticky="nsew")
        self._current = index
        self._nav_rail.set_active(index)

        # Refresh history when navigating there
        if index == 1:
            self._dl_screen.refresh_files()
            self._refresh_library_summary()
        if index == 2:
            self._hist_screen.refresh()

    def _refresh_library_summary(self) -> None:
        folder = self._settings.get("download_dir")
        count = len(scan_audio_files(folder))
        self._nav_rail.set_library_summary(count, Path(folder).name or str(folder))

    # ═════════════════════════════ EVENT ROUTING ══════════════════════════════

    def _on_download_started(self) -> None:
        """Called by HomeScreen when a download is initiated."""
        if self._home_screen._video_info:
            title = self._home_screen._video_info.title
        else:
            title = "Downloading..."
        self._dl_idx = self._dl_screen.add_download(
            title=title,
            url=self._home_screen._url_var.get(),
        )

    def _on_dl_event(self, payload: dict) -> None:
        """
        Central dispatcher for all yt-dlp events.
        Runs on the Tk main thread (via root.after in DownloadManager._poll).
        """
        t = payload.get("type")

        # ── Forward to home screen ────────────────────────────────────────────
        if t in ("info", "progress", "finished", "error"):
            self._home_screen.handle_event(payload)

        # ── Update downloads screen ───────────────────────────────────────────
        if t == "progress" and self._dl_idx >= 0:
            self._dl_screen.update_download(
                idx      = self._dl_idx,
                pct      = payload.get("percent", 0),
                speed    = payload.get("speed", ""),
                eta      = payload.get("eta", "--"),
                size_str = f"{payload.get('downloaded','')} / {payload.get('total','')}",
                status   = "downloading",
            )

        if t == "finished" and self._dl_idx >= 0:
            self._dl_screen.update_download(
                idx      = self._dl_idx,
                pct      = 100,
                speed    = "",
                eta      = "Done",
                size_str = "",
                status   = "done",
            )
            # Refresh history badge
            self._hist_screen.refresh()
            self._dl_screen.refresh_files()
            self._refresh_library_summary()
            self._dl_idx = -1

        if t == "error" and self._dl_idx >= 0:
            self._dl_screen.update_download(
                idx      = self._dl_idx,
                pct      = self._dl_screen._entries[self._dl_idx].percent
                           if self._dl_screen._entries else 0,
                speed    = "",
                eta      = "--",
                size_str = "",
                status   = "error",
            )
            self._dl_idx = -1
