"""
ui/screens/home_screen.py
─────────────────────────────────────────────────────────────────────────────
Home screen for Ploxt Desktop.
Includes advanced audio format selection and a mini music player.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import Optional, Callable
import threading
import urllib.request
import os

import customtkinter as ctk
from PIL import Image, ImageDraw
import io
from pygame import mixer

from core.theme import ThemeManager, TypeScale, Shape
from core.downloader import DownloadManager, VideoInfo
from core.history import HistoryManager
from core.settings import AppSettings
from ui.components.m3_widgets import (
    M3Card, M3FilledButton, M3TonalButton, M3OutlinedButton,
    M3TextField, M3LinearProgress, M3SectionLabel, M3DropdownMenu,
    M3StatusBadge, M3Divider,
)


# ─────────────────────────────── Thumbnail Helper ────────────────────────────

def _load_thumbnail(url: str, size: tuple[int,int] = (160, 90)) -> Optional[ctk.CTkImage]:
    """Fetch a thumbnail from a URL and return a CTkImage, or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img = img.resize(size, Image.LANCZOS)
        # Rounded corners
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, *size], radius=12, fill=255)
        img.putalpha(mask)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        return None


# ─────────────────────────────── HomeScreen ──────────────────────────────────

class HomeScreen(ctk.CTkScrollableFrame):
    """
    The primary screen of Ploxt Desktop.
    """

    def __init__(
        self,
        master,
        download_mgr    : DownloadManager,
        history_mgr     : HistoryManager,
        settings        : AppSettings,
        on_download_start: Optional[Callable] = None,
        **kwargs,
    ):
        s = ThemeManager.scheme
        kwargs.setdefault("fg_color", s.surface)
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("scrollbar_button_color", s.outline_variant)
        super().__init__(master, **kwargs)

        self._dl_mgr   = download_mgr
        self._hist_mgr = history_mgr
        self._settings = settings
        self._on_dl_start = on_download_start

        # State
        self._video_info : Optional[VideoInfo] = None
        self._selected_fmt: str = "bestvideo+bestaudio/best"
        self._is_fetching : bool = False
        self._is_downloading: bool = False
        self._audio_format_choice: str = "mp3"
        self._last_downloaded_file: Optional[str] = None
        self._current_download_fmt: str = self._selected_fmt
        self._current_audio_codec: str = self._audio_format_choice

        # Initialize the audio preview player.
        try:
            mixer.init()
        except Exception:
            pass

        self._build_ui()

    # ═════════════════════════════ UI CONSTRUCTION ════════════════════════════

    def _build_ui(self) -> None:
        s = ThemeManager.scheme
        self.columnconfigure(0, weight=1)

        # ── Hero header ──────────────────────────────────────────────────────
        header = ctk.CTkLabel(
            self,
            text="Ploxt Desktop",
            font=ctk.CTkFont("", 28, "bold"),
            text_color=s.primary,
        )
        header.grid(row=0, column=0, sticky="w", padx=32, pady=(32, 4))

        sub = ctk.CTkLabel(
            self,
            text="Download videos and audio from anywhere",
            font=ctk.CTkFont(*TypeScale.body_large),
            text_color=s.on_surface_var,
        )
        sub.grid(row=1, column=0, sticky="w", padx=32, pady=(0, 24))

        # ── URL Input Card ────────────────────────────────────────────────────
        self._build_url_card()

        # ── Video Info Card (hidden until fetch succeeds) ─────────────────────
        self._build_info_card()

        # ── Progress Card (hidden until download starts) ──────────────────────
        self._build_progress_card()

        # ── Mini Music Player Card (hidden until an audio is downloaded) ──────
        self._build_player_card()

        # ── Quick-tip ─────────────────────────────────────────────────────────
        tip = ctk.CTkLabel(
            self,
            text="Supports YouTube, Twitter/X, TikTok, Instagram, Vimeo, and 1000+ more sites",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var,
            wraplength=600,
            justify="center",
        )
        tip.grid(row=10, column=0, pady=(12, 32))

    # ── URL Input card ────────────────────────────────────────────────────────

    def _build_url_card(self) -> None:
        s = ThemeManager.scheme

        card = M3Card(self)
        card.grid(row=2, column=0, padx=32, pady=8, sticky="ew")
        card.columnconfigure(0, weight=1)

        lbl = M3SectionLabel(card, text="Video URL")
        lbl.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(20, 6))

        # URL field + Paste button row
        self._url_var = tk.StringVar()
        self._url_entry = M3TextField(
            card,
            placeholder="https://www.youtube.com/watch?v=...",
        )
        self._url_entry.configure(textvariable=self._url_var, height=48)
        self._url_entry.bind_focus_effects()
        self._url_entry.grid(row=1, column=0, sticky="ew", padx=(20, 8), pady=4)

        paste_btn = M3TonalButton(card, text="Paste", width=96)
        paste_btn.configure(command=self._paste_from_clipboard)
        paste_btn.grid(row=1, column=1, padx=(0, 8), pady=4)

        clear_btn = M3OutlinedButton(card, text="Clear", width=56)
        clear_btn.configure(command=lambda: self._url_var.set(""))
        clear_btn.grid(row=1, column=2, padx=(0, 20), pady=4)

        # Analyze / Fetch button
        self._analyze_btn = M3FilledButton(
            card, text="Analyze URL",
            command=self._on_analyze_click,
        )
        self._analyze_btn.grid(
            row=2, column=0, columnspan=3,
            padx=20, pady=(8, 20), sticky="ew",
        )

    # ── Video Info card ───────────────────────────────────────────────────────

    def _build_info_card(self) -> None:
        s = ThemeManager.scheme

        self._info_card = M3Card(self)
        self._info_card.columnconfigure(1, weight=1)

        # Thumbnail
        self._thumb_label = ctk.CTkLabel(
            self._info_card, text="",
            width=160, height=90,
        )
        self._thumb_label.grid(row=0, column=0, rowspan=3, padx=20, pady=20, sticky="nw")

        # Title
        self._title_label = ctk.CTkLabel(
            self._info_card, text="",
            font=ctk.CTkFont(*TypeScale.title_medium),
            text_color=s.on_surface,
            wraplength=380,
            justify="left",
            anchor="w",
        )
        self._title_label.grid(row=0, column=1, sticky="w", padx=(0,20), pady=(20,2))

        # Meta (uploader - duration)
        self._meta_label = ctk.CTkLabel(
            self._info_card, text="",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var,
            anchor="w",
        )
        self._meta_label.grid(row=1, column=1, sticky="w", padx=(0,20))

        # Quality & Format Selection Rows
        selectors_frame = ctk.CTkFrame(self._info_card, fg_color="transparent")
        selectors_frame.grid(row=2, column=1, sticky="ew", padx=(0,20), pady=(8,0))
        selectors_frame.columnconfigure(1, weight=1)

        # Row 1: Video Quality
        M3SectionLabel(selectors_frame, text="Video Quality").grid(row=0, column=0, padx=(0,8), sticky="w")
        self._fmt_menu = M3DropdownMenu(
            selectors_frame,
            values=["Best (auto)"],
            command=self._on_format_selected,
        )
        self._fmt_menu.grid(row=0, column=1, sticky="ew", pady=4)

        # Row 2: Audio format picker
        M3SectionLabel(selectors_frame, text="Audio Format").grid(row=1, column=0, padx=(0,8), sticky="w")
        self._audio_fmt_menu = M3DropdownMenu(
            selectors_frame,
            values=["mp3 (Popular)", "opus (High compression)", "flac (Lossless)"],
            command=self._on_audio_format_selected,
        )
        self._audio_fmt_menu.grid(row=1, column=1, sticky="ew", pady=4)
        self._audio_fmt_menu.set("mp3 (Popular)")

        M3Divider(self._info_card).grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=12)

        # Output dir row
        dir_row = ctk.CTkFrame(self._info_card, fg_color="transparent")
        dir_row.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=(0,4))
        dir_row.columnconfigure(1, weight=1)

        M3SectionLabel(dir_row, text="Save to").grid(row=0, column=0, padx=(0,8))
        self._dir_var = tk.StringVar(value=self._settings.get("download_dir"))
        dir_entry = M3TextField(dir_row, placeholder="Output folder")
        dir_entry.configure(textvariable=self._dir_var, height=36)
        dir_entry.grid(row=0, column=1, sticky="ew", padx=(0,8))

        browse_btn = M3OutlinedButton(dir_row, text="Browse", width=84)
        browse_btn.configure(command=self._browse_output_dir)
        browse_btn.grid(row=0, column=2)

        # Action buttons
        btn_row = ctk.CTkFrame(self._info_card, fg_color="transparent")
        btn_row.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=(8,20))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        self._dl_btn = M3FilledButton(btn_row, text="Download Video")
        self._dl_btn.configure(command=self._on_download_click)
        self._dl_btn.grid(row=0, column=0, sticky="ew", padx=(0,8))

        self._audio_btn = M3TonalButton(btn_row, text="Download Audio Only")
        self._audio_btn.configure(command=self._on_audio_only_click)
        self._audio_btn.grid(row=0, column=1, sticky="ew")

    # ── Progress card ─────────────────────────────────────────────────────────

    def _build_progress_card(self) -> None:
        s = ThemeManager.scheme

        self._prog_card = M3Card(self)
        self._prog_card.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(self._prog_card, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(16,4))
        hdr.columnconfigure(0, weight=1)

        self._prog_title = ctk.CTkLabel(
            hdr, text="Downloading...",
            font=ctk.CTkFont(*TypeScale.title_small),
            text_color=s.on_surface, anchor="w",
        )
        self._prog_title.grid(row=0, column=0, sticky="w")

        self._prog_badge = M3StatusBadge(hdr, status="downloading")
        self._prog_badge.grid(row=0, column=1)

        self._prog_bar = M3LinearProgress(self._prog_card)
        self._prog_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=8)

        stats_row = ctk.CTkFrame(self._prog_card, fg_color="transparent")
        stats_row.grid(row=2, column=0, sticky="ew", padx=20, pady=(0,16))
        stats_row.columnconfigure(1, weight=1)

        self._pct_label = ctk.CTkLabel(
            stats_row, text="0%",
            font=ctk.CTkFont("", 22, "bold"),
            text_color=s.primary, width=60,
        )
        self._pct_label.grid(row=0, column=0)

        stat_mid = ctk.CTkFrame(stats_row, fg_color="transparent")
        stat_mid.grid(row=0, column=1, sticky="ew", padx=8)

        self._size_label = ctk.CTkLabel(
            stat_mid, text="0 B / ?",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var, anchor="w",
        )
        self._size_label.pack(anchor="w")

        self._speed_label = ctk.CTkLabel(
            stat_mid, text="",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var, anchor="w",
        )
        self._speed_label.pack(anchor="w")

        self._eta_label = ctk.CTkLabel(
            stats_row, text="ETA --:--",
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var,
        )
        self._eta_label.grid(row=0, column=2)

    # ── Mini Music Player card ───────────────────────────────────────────────

    def _build_player_card(self) -> None:
        s = ThemeManager.scheme

        self._player_card = M3Card(self)
        self._player_card.configure(fg_color=s.secondary_cont)
        self._player_card.columnconfigure(0, weight=1)

        player_header = ctk.CTkLabel(
            self._player_card, text="Mini Music Player",
            font=ctk.CTkFont(*TypeScale.label_large),
            text_color=s.on_secondary_cont
        )
        player_header.grid(row=0, column=0, sticky="w", padx=20, pady=(16,4))

        self._track_title_label = ctk.CTkLabel(
            self._player_card, text="No audio file loaded",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_secondary_cont,
            wraplength=500, justify="left"
        )
        self._track_title_label.grid(row=1, column=0, sticky="w", padx=20, pady=4)

        # Play / Pause / Stop controls
        ctrl_frame = ctk.CTkFrame(self._player_card, fg_color="transparent")
        ctrl_frame.grid(row=2, column=0, sticky="w", padx=20, pady=(4, 16))

        self._play_btn = M3FilledButton(ctrl_frame, text="Play", width=80, command=self._toggle_playback)
        self._play_btn.pack(side="left", padx=(0, 8))

        self._stop_btn = M3OutlinedButton(ctrl_frame, text="Stop", width=80, command=self._stop_playback)
        self._stop_btn.pack(side="left")

    # ═════════════════════════════ EVENT HANDLERS ═════════════════════════════

    def _paste_from_clipboard(self) -> None:
        try:
            clip = self.clipboard_get()
            self._url_var.set(clip.strip())
        except Exception:
            pass

    def _browse_output_dir(self) -> None:
        d = filedialog.askdirectory(
            initialdir=self._dir_var.get() or str(Path.home()),
            title="Select download folder",
        )
        if d:
            self._dir_var.set(d)
            self._settings.set("download_dir", d)

    def _on_format_selected(self, choice: str) -> None:
        """Map human-readable label back to format_id."""
        if self._video_info is None:
            return
        for fmt in self._video_info.best_formats:
            if fmt.label == choice or fmt.resolution == choice:
                self._selected_fmt = fmt.format_id
                return
        self._selected_fmt = "bestvideo+bestaudio/best"

    def _on_audio_format_selected(self, choice: str) -> None:
        """Extract the audio codec from the dropdown label."""
        self._audio_format_choice = choice.split(" ")[0].strip().lower()

    def _on_analyze_click(self) -> None:
        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please paste or type a video URL first.")
            return
        if self._is_fetching or self._is_downloading:
            return

        self._is_fetching = True
        self._hide_info_card()
        self._hide_progress_card()
        self._hide_player_card()

        self._analyze_btn.configure(
            text="Fetching info...", state="disabled"
        )
        self._dl_mgr.fetch_info(url)

    def _on_download_click(self) -> None:
        self._start_download(self._selected_fmt)

    def _on_audio_only_click(self) -> None:
        fmt_id = f"bestaudio/best"
        self._settings.set("audio_codec_override", self._audio_format_choice)
        self._start_download(fmt_id, self._audio_format_choice)

    def _start_download(self, fmt_id: str, audio_codec: Optional[str] = None) -> None:
        if self._video_info is None or self._is_downloading:
            return

        audio_codec = (audio_codec or self._audio_format_choice).lower()
        out_dir = Path(self._dir_var.get() or self._settings.get("download_dir"))
        self._is_downloading = True
        self._current_download_fmt = fmt_id
        self._current_audio_codec = audio_codec
        self._dl_btn.configure(state="disabled")
        self._audio_btn.configure(state="disabled")

        self._show_progress_card()
        self._prog_title.configure(text=f"Downloading - {self._video_info.title[:55]}...")
        self._prog_badge.set_status("downloading")

        if self._on_dl_start:
            self._on_dl_start()

        self._dl_mgr.start_download(self._video_info, fmt_id, out_dir, audio_codec)

    # ═════════════════════════════ EVENT DISPATCHER ═══════════════════════════

    def handle_event(self, payload: dict) -> None:
        """Called by AppWindow when a downloader event arrives."""
        t = payload.get("type")

        if t == "info":
            self._on_info_received(payload["data"])
        elif t == "progress":
            self._on_progress(payload)
        elif t == "finished":
            self._on_finished(payload)
        elif t == "error":
            self._on_error(payload["message"])

    def _on_info_received(self, info: VideoInfo) -> None:
        self._is_fetching = False
        self._video_info  = info

        self._analyze_btn.configure(text="Analyze URL", state="normal")

        # ── Populate info card ───────────────────────────────────────────────
        self._title_label.configure(text=info.title)
        views = f"{info.view_count:,}" if info.view_count else "?"
        self._meta_label.configure(
            text=f"{info.uploader}  -  {info.duration_str}  -  {views} views"
        )

        # Populate format menu
        fmts = info.best_formats
        labels = [f.label for f in fmts]
        self._fmt_menu.configure(values=labels)
        if labels:
            self._fmt_menu.set(labels[0])
            self._selected_fmt = fmts[0].format_id

        self._show_info_card()

        # Load thumbnail in background
        if info.thumbnail_url:
            threading.Thread(
                target=self._fetch_thumbnail,
                args=(info.thumbnail_url,),
                daemon=True,
            ).start()

    def _fetch_thumbnail(self, url: str) -> None:
        img = _load_thumbnail(url)
        if img:
            self._thumb_label.configure(image=img)

    def _on_progress(self, p: dict) -> None:
        pct = p.get("percent", 0.0)
        self._prog_bar.set(pct / 100)
        self._pct_label.configure(text=f"{pct:.0f}%")
        self._size_label.configure(text=f"{p.get('downloaded','')} / {p.get('total','')}")
        self._speed_label.configure(text=p.get("speed", ""))
        self._eta_label.configure(text=f"ETA {p.get('eta','--')}")

    def _on_finished(self, payload: dict) -> None:
        self._is_downloading = False
        self._prog_bar.set(1.0)
        self._pct_label.configure(text="100%")
        self._prog_badge.set_status("done")
        self._prog_title.configure(text="Download complete")
        self._eta_label.configure(text="Done")
        self._speed_label.configure(text="")

        self._dl_btn.configure(state="normal")
        self._audio_btn.configure(state="normal")

        file_path = payload.get("filepath") or payload.get("file_path")
        
        if self._video_info:
            self._hist_mgr.add(
                title    = self._video_info.title,
                url      = self._video_info.url,
                fmt      = (
                    f"{self._current_download_fmt} ({self._current_audio_codec})"
                    if "audio" in self._current_download_fmt
                    else self._current_download_fmt
                ),
                out_path = payload.get("out_dir", ""),
                status   = "completed",
            )
            
            if not file_path:
                out_dir = self._dir_var.get() or self._settings.get("download_dir")
                for ext in ['.mp3', '.opus', '.flac', '.wav', '.m4a']:
                    possible_file = os.path.join(out_dir, f"{self._video_info.title}{ext}")
                    if os.path.exists(possible_file):
                        file_path = possible_file
                        break

        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path)
            if filename.lower().endswith(('.mp3', '.opus', '.flac', '.wav', '.m4a')):
                self._last_downloaded_file = file_path
                self._track_title_label.configure(text=filename)
                self._show_player_card()

    def _on_error(self, message: str) -> None:
        self._is_fetching   = False
        self._is_downloading = False
        self._analyze_btn.configure(text="Analyze URL", state="normal")
        self._dl_btn.configure(state="normal")
        self._audio_btn.configure(state="normal")

        if self._prog_card.winfo_ismapped():
            self._prog_badge.set_status("error")
            self._prog_title.configure(text="Error")

        messagebox.showerror("Ploxt - Error", message)

    # ── Music player controls ────────────────────────────────────────────────

    def _toggle_playback(self) -> None:
        if not self._last_downloaded_file:
            return

        if self._play_btn.cget("text") == "Play":
            try:
                if mixer.music.get_busy():
                    mixer.music.unpause()
                else:
                    mixer.music.load(self._last_downloaded_file)
                    mixer.music.play()
                self._play_btn.configure(text="Pause")
            except Exception as e:
                self._track_title_label.configure(text=f"Preview is not supported for this codec: {os.path.basename(self._last_downloaded_file)}")
        else:
            mixer.music.pause()
            self._play_btn.configure(text="Play")

    def _stop_playback(self) -> None:
        try:
            mixer.music.stop()
        except Exception:
            pass
        self._play_btn.configure(text="Play")

    # ═════════════════════════════ CARD VISIBILITY ════════════════════════════

    def _show_info_card(self) -> None:
        self._info_card.grid(row=3, column=0, padx=32, pady=8, sticky="ew")

    def _hide_info_card(self) -> None:
        self._info_card.grid_forget()

    def _show_progress_card(self) -> None:
        self._prog_card.grid(row=4, column=0, padx=32, pady=8, sticky="ew")

    def _hide_progress_card(self) -> None:
        self._prog_card.grid_forget()

    def _show_player_card(self) -> None:
        self._player_card.grid(row=5, column=0, padx=32, pady=8, sticky="ew")

    def _hide_player_card(self) -> None:
        self._player_card.grid_forget()
