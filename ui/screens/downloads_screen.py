"""
ui/screens/downloads_screen.py
─────────────────────────────────────────────────────────────────────────────
Active Downloads screen.

Displays all in-progress and recently-completed downloads as individual
M3Card rows, each with a progress bar, speed, and ETA.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import customtkinter as ctk
from pygame import mixer

from core.theme import ThemeManager, TypeScale, Shape
from core.settings import AppSettings
from core.library import AudioFile, scan_audio_files
from ui.components.m3_widgets import (
    M3Card, M3LinearProgress, M3StatusBadge, M3Divider,
    M3FilledButton, M3OutlinedButton,
)


@dataclass
class DownloadEntry:
    title    : str
    url      : str
    percent  : float = 0.0
    speed    : str   = ""
    eta      : str   = "--:--"
    status   : str   = "pending"    # pending | downloading | done | error
    size_str : str   = ""
    widgets  : dict  = field(default_factory=dict)


class _DownloadRow(M3Card):
    """A single active-download card widget."""

    def __init__(self, master, entry: DownloadEntry, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("height", 110)
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self._entry = entry
        self._build()

    def _build(self) -> None:
        s = ThemeManager.scheme
        e = self._entry

        # Title row
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        hdr.columnconfigure(0, weight=1)

        self._title_lbl = ctk.CTkLabel(
            hdr, text=e.title[:72],
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface, anchor="w",
        )
        self._title_lbl.grid(row=0, column=0, sticky="w")

        self._badge = M3StatusBadge(hdr, status=e.status)
        self._badge.grid(row=0, column=1, padx=(8,0))

        # Progress bar
        self._pbar = M3LinearProgress(self)
        self._pbar.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        self._pbar.set(e.percent / 100)

        # Stats row
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))
        stats.columnconfigure(1, weight=1)

        self._pct_lbl = ctk.CTkLabel(
            stats, text=f"{e.percent:.0f}%",
            font=ctk.CTkFont("", 13, "bold"),
            text_color=s.primary, width=44,
        )
        self._pct_lbl.grid(row=0, column=0)

        self._size_lbl = ctk.CTkLabel(
            stats, text=e.size_str,
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var, anchor="w",
        )
        self._size_lbl.grid(row=0, column=1, sticky="w", padx=4)

        self._speed_lbl = ctk.CTkLabel(
            stats, text=e.speed,
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var,
        )
        self._speed_lbl.grid(row=0, column=2, padx=(0,8))

        self._eta_lbl = ctk.CTkLabel(
            stats, text=f"ETA {e.eta}",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var,
        )
        self._eta_lbl.grid(row=0, column=3)

    def update_progress(self, pct: float, speed: str, eta: str, size_str: str, status: str) -> None:
        self._pbar.set(pct / 100)
        self._pct_lbl.configure(text=f"{pct:.0f}%")
        self._size_lbl.configure(text=size_str)
        self._speed_lbl.configure(text=speed)
        self._eta_lbl.configure(text=f"ETA {eta}")
        self._badge.set_status(status)
        self._entry.status = status


class _AudioFileRow(M3Card):
    """A compact row for an audio file already present in the output folder."""

    def __init__(self, master, audio: AudioFile, on_play: callable, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("height", 82)
        kwargs.setdefault("fg_color", s.surface_container)
        super().__init__(master, **kwargs)
        self.columnconfigure(1, weight=1)
        self._audio = audio
        self._on_play = on_play
        self._selected = False
        try:
            self.configure(cursor="hand2")
        except Exception:
            pass
        self._build()
        self._bind_interactions()

    def _build(self) -> None:
        s = ThemeManager.scheme
        a = self._audio

        badge = ctk.CTkLabel(
            self,
            text=a.ext,
            width=56,
            height=32,
            fg_color=s.tertiary_cont,
            text_color=s.on_surface,
            corner_radius=Shape.full,
            font=ctk.CTkFont(*TypeScale.label_small),
        )
        badge.grid(row=0, column=0, rowspan=2, padx=(16, 10), pady=14)

        ctk.CTkLabel(
            self,
            text=a.title[:72],
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface,
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", pady=(14, 2))

        modified = datetime.fromtimestamp(a.modified_ts).strftime("%d %b %Y  %H:%M")
        meta = f"{a.size_str}  -  {modified}"
        ctk.CTkLabel(
            self,
            text=meta,
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var,
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", pady=(0, 14))

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        s = ThemeManager.scheme
        self.configure(fg_color=s.secondary_cont if selected else s.surface_container)

    def _bind_interactions(self) -> None:
        for widget in (self, *self.winfo_children()):
            try:
                widget.configure(cursor="hand2")
            except Exception:
                pass
            widget.bind("<Button-1>", lambda _e: self._on_play(self._audio, self))
            widget.bind("<Enter>", lambda _e: self._set_hover(True))
            widget.bind("<Leave>", lambda _e: self._set_hover(False))

    def _set_hover(self, is_hovered: bool) -> None:
        if self._selected:
            return
        s = ThemeManager.scheme
        self.configure(fg_color=s.surface_variant if is_hovered else s.surface_container)


class DownloadsScreen(ctk.CTkScrollableFrame):
    """Active downloads list screen."""

    def __init__(self, master, settings: AppSettings, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("fg_color", s.surface)
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("scrollbar_button_color", s.outline_variant)
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)

        self._settings = settings
        self._entries: list[DownloadEntry] = []
        self._rows: list[_DownloadRow]     = []
        self._audio_files: list[AudioFile] = []
        self._audio_rows: list[_AudioFileRow] = []
        self._selected_audio: AudioFile | None = None
        self._selected_row: _AudioFileRow | None = None
        self._paused = False

        try:
            mixer.init()
        except Exception:
            pass

        self._build_header()
        self._build_active_section()
        self._build_player_section()
        self._build_library_section()
        self.refresh_files()

    def _build_header(self) -> None:
        s = ThemeManager.scheme
        ctk.CTkLabel(
            self, text="Downloads",
            font=ctk.CTkFont("", 28, "bold"),
            text_color=s.on_surface, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=32, pady=(32, 4))

        self._count_lbl = ctk.CTkLabel(
            self, text="No active downloads",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface_var, anchor="w",
        )
        self._count_lbl.grid(row=1, column=0, sticky="w", padx=32, pady=(0, 20))

    def _build_active_section(self) -> None:
        s = ThemeManager.scheme
        self._active_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._active_frame.grid(row=2, column=0, sticky="ew", padx=32, pady=(0, 12))
        self._active_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._active_frame,
            text="Active downloads",
            font=ctk.CTkFont(*TypeScale.title_small),
            text_color=s.on_surface_var,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self._active_empty_lbl = ctk.CTkLabel(
            self._active_frame,
            text="Nothing downloading right now.",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface_var,
            anchor="w",
        )
        self._active_empty_lbl.grid(row=1, column=0, sticky="ew", pady=8)
        self._list_start_row = 2

    def _build_player_section(self) -> None:
        s = ThemeManager.scheme
        self._player_card = M3Card(self)
        self._player_card.configure(fg_color=s.secondary_cont)
        self._player_card.grid(row=3, column=0, sticky="ew", padx=32, pady=(0, 12))
        self._player_card.columnconfigure(0, weight=1)

        self._now_title = ctk.CTkLabel(
            self._player_card,
            text="Select a file to play",
            font=ctk.CTkFont(*TypeScale.title_small),
            text_color=s.on_secondary_cont,
            anchor="w",
        )
        self._now_title.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 2))

        self._now_meta = ctk.CTkLabel(
            self._player_card,
            text="Local audio library",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_secondary_cont,
            anchor="w",
        )
        self._now_meta.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))

        controls = ctk.CTkFrame(self._player_card, fg_color="transparent")
        controls.grid(row=0, column=1, rowspan=2, sticky="e", padx=18, pady=12)

        self._play_pause_btn = M3FilledButton(
            controls,
            text="Play",
            width=84,
            command=self._toggle_playback,
        )
        self._play_pause_btn.pack(side="left", padx=(0, 8))

        self._stop_btn = M3OutlinedButton(
            controls,
            text="Stop",
            width=76,
            command=self._stop_playback,
        )
        self._stop_btn.pack(side="left")

    def _build_library_section(self) -> None:
        s = ThemeManager.scheme
        self._library_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._library_frame.grid(row=4, column=0, sticky="ew", padx=32, pady=(10, 32))
        self._library_frame.columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self._library_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Files in folder",
            font=ctk.CTkFont(*TypeScale.title_small),
            text_color=s.on_surface_var,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._library_count_lbl = ctk.CTkLabel(
            header,
            text="Scanning...",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var,
        )
        self._library_count_lbl.grid(row=0, column=1, sticky="e")

        M3Divider(self._library_frame).grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self._library_list = ctk.CTkFrame(self._library_frame, fg_color="transparent")
        self._library_list.grid(row=2, column=0, sticky="ew")
        self._library_list.columnconfigure(0, weight=1)

        self._library_empty_lbl = ctk.CTkLabel(
            self._library_list,
            text="No audio files found in the Ploxt folder yet.",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface_var,
            anchor="w",
        )

    def add_download(self, title: str, url: str) -> int:
        """Register a new download entry; returns its index."""
        entry = DownloadEntry(title=title, url=url, status="downloading")
        idx   = len(self._entries)
        self._entries.append(entry)

        row = _DownloadRow(self._active_frame, entry)
        row.grid(row=self._list_start_row + idx, column=0,
                 pady=6, sticky="ew")
        self._rows.append(row)

        self._active_empty_lbl.grid_forget()
        self._update_count()
        return idx

    def update_download(
        self, idx: int,
        pct: float, speed: str, eta: str,
        size_str: str, status: str,
    ) -> None:
        if 0 <= idx < len(self._rows):
            self._rows[idx].update_progress(pct, speed, eta, size_str, status)
            if status in ("done", "error"):
                self._update_count()

    def refresh_files(self) -> list[AudioFile]:
        """Scan the configured output folder and render the local audio list."""
        folder = self._settings.get("download_dir")
        self._audio_files = scan_audio_files(folder)

        for widget in self._library_list.winfo_children():
            widget.destroy()
        self._audio_rows = []
        self._selected_row = None

        if not self._audio_files:
            self._library_empty_lbl = ctk.CTkLabel(
                self._library_list,
                text="No audio files found in the Ploxt folder yet.",
                font=ctk.CTkFont(*TypeScale.body_medium),
                text_color=ThemeManager.scheme.on_surface_var,
                anchor="w",
            )
            self._library_empty_lbl.grid(row=0, column=0, sticky="ew", pady=10)
            self._library_count_lbl.configure(text="0 files")
            return []

        for i, audio in enumerate(self._audio_files):
            row = _AudioFileRow(self._library_list, audio, on_play=self._play_audio)
            row.grid(row=i, column=0, sticky="ew", pady=5)
            if self._selected_audio and audio.path == self._selected_audio.path:
                row.set_selected(True)
                self._selected_row = row
            self._audio_rows.append(row)

        self._library_count_lbl.configure(text=f"{len(self._audio_files)} files")
        return list(self._audio_files)

    def _play_audio(self, audio: AudioFile, row: _AudioFileRow) -> None:
        if self._selected_row and self._selected_row is not row:
            self._selected_row.set_selected(False)
        self._selected_audio = audio
        self._selected_row = row
        row.set_selected(True)
        self._paused = False

        self._now_title.configure(text=audio.title[:84])
        self._now_meta.configure(text=f"{audio.ext}  -  {audio.size_str}")
        self._play_pause_btn.configure(text="Pause")

        try:
            mixer.music.load(str(audio.path))
            mixer.music.play()
        except Exception:
            self._now_meta.configure(text=f"Preview is not supported for {audio.ext}")
            self._play_pause_btn.configure(text="Play")

    def _toggle_playback(self) -> None:
        if self._selected_audio is None:
            return
        try:
            if self._paused:
                mixer.music.unpause()
                self._paused = False
                self._play_pause_btn.configure(text="Pause")
            elif mixer.music.get_busy():
                mixer.music.pause()
                self._paused = True
                self._play_pause_btn.configure(text="Play")
            else:
                mixer.music.load(str(self._selected_audio.path))
                mixer.music.play()
                self._paused = False
                self._play_pause_btn.configure(text="Pause")
        except Exception:
            self._now_meta.configure(text=f"Preview is not supported for {self._selected_audio.ext}")

    def _stop_playback(self) -> None:
        try:
            mixer.music.stop()
        except Exception:
            pass
        self._paused = False
        self._play_pause_btn.configure(text="Play")

    def _update_count(self) -> None:
        active = sum(1 for e in self._entries if e.status == "downloading")
        total  = len(self._entries)
        if total == 0:
            self._count_lbl.configure(text="No active downloads")
        else:
            self._count_lbl.configure(
                text=f"{active} active  -  {total} total"
            )
