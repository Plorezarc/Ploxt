"""
ui/screens/settings_screen.py
─────────────────────────────────────────────────────────────────────────────
Settings screen — mirrors Ploxt's Settings page.

Sections
  • Appearance   : Dark/Light mode toggle
  • Download     : Default output folder, default format
  • Network      : HTTP proxy
  • About        : Version, source link
"""

from __future__ import annotations
from tkinter import filedialog
import tkinter as tk
from pathlib import Path
import customtkinter as ctk

from core.theme import ThemeManager, TypeScale, Shape
from core.settings import AppSettings
from ui.components.m3_widgets import (
    M3Card, M3SectionLabel, M3FilledButton, M3OutlinedButton,
    M3TextField, M3DropdownMenu, M3Divider,
)

APP_VERSION = "1.0.0-alpha"


class _SettingsSection(M3Card):
    """A titled settings card grouping related options."""

    def __init__(self, master, title: str, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        s = ThemeManager.scheme

        ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(*TypeScale.title_small),
            text_color=s.primary, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4))

        M3Divider(self).grid(row=1, column=0, sticky="ew", padx=20, pady=(0,8))
        self._row = 2

    def add_row(self, widget: ctk.CTkBaseClass, **grid_kw) -> None:
        grid_kw.setdefault("row", self._row)
        grid_kw.setdefault("column", 0)
        grid_kw.setdefault("sticky", "ew")
        grid_kw.setdefault("padx", 20)
        grid_kw.setdefault("pady", 4)
        widget.grid(**grid_kw)
        self._row += 1

    def add_spacer(self) -> None:
        ctk.CTkFrame(self, fg_color="transparent", height=8).grid(
            row=self._row, column=0
        )
        self._row += 1


def _labeled_row(parent, label: str, widget: ctk.CTkBaseClass) -> ctk.CTkFrame:
    """Returns a two-column frame with a label on the left."""
    s = ThemeManager.scheme
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.columnconfigure(1, weight=1)
    ctk.CTkLabel(
        row, text=label,
        font=ctk.CTkFont(*TypeScale.body_medium),
        text_color=s.on_surface, width=140, anchor="w",
    ).grid(row=0, column=0, sticky="w")
    widget.grid(row=0, column=1, sticky="ew", padx=(8,0))
    return row


class SettingsScreen(ctk.CTkScrollableFrame):
    """Settings screen."""

    def __init__(self, master, settings: AppSettings, root, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("fg_color", s.surface)
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("scrollbar_button_color", s.outline_variant)
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)

        self._settings = settings
        self._win      = root   # renamed: avoid collision with Tkinter's _root()
        self._build()

    def _build(self) -> None:
        s = ThemeManager.scheme
        ctk.CTkLabel(
            self, text="Settings",
            font=ctk.CTkFont("", 28, "bold"),
            text_color=s.on_surface, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=32, pady=(32, 20))

        # ── Appearance ───────────────────────────────────────────────────────
        appear = _SettingsSection(self, "Appearance")
        appear.grid(row=1, column=0, padx=32, pady=8, sticky="ew")

        mode_row = ctk.CTkFrame(appear, fg_color="transparent")
        mode_row.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            mode_row, text="Theme",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._mode_switch = ctk.CTkSwitch(
            mode_row,
            text="Dark mode",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface,
            progress_color=s.primary,
            command=self._toggle_theme,
        )
        if ThemeManager.is_dark():
            self._mode_switch.select()
        self._mode_switch.grid(row=0, column=1)
        appear.add_row(mode_row)
        appear.add_spacer()

        # ── Download ─────────────────────────────────────────────────────────
        dl = _SettingsSection(self, "Download")
        dl.grid(row=2, column=0, padx=32, pady=8, sticky="ew")

        # Output folder
        dir_row = ctk.CTkFrame(dl, fg_color="transparent")
        dir_row.columnconfigure(1, weight=1)
        ctk.CTkLabel(
            dir_row, text="Output folder",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface, width=120, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._dir_var = tk.StringVar(value=self._settings.get("download_dir"))
        dir_entry = M3TextField(dir_row, placeholder="~/Downloads/Ploxt")
        dir_entry.configure(textvariable=self._dir_var, height=38)
        dir_entry.grid(row=0, column=1, sticky="ew", padx=(8,8))

        M3OutlinedButton(
            dir_row, text="Browse", width=84, height=38,
            command=self._browse_dir,
        ).grid(row=0, column=2)
        dl.add_row(dir_row)

        # Default format
        fmt_row = ctk.CTkFrame(dl, fg_color="transparent")
        fmt_row.columnconfigure(1, weight=1)
        ctk.CTkLabel(
            fmt_row, text="Default format",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface, width=120, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._fmt_menu = M3DropdownMenu(
            fmt_row,
            values=["Best (auto)", "1080p", "720p", "480p", "Audio Only (MP3)"],
            command=self._on_fmt_change,
        )
        self._fmt_menu.set("Best (auto)")
        self._fmt_menu.grid(row=0, column=1, sticky="ew", padx=(8,0))
        dl.add_row(fmt_row)

        # Open folder after download
        self._open_var = tk.BooleanVar(value=self._settings.get("open_folder_after", True))
        open_switch = ctk.CTkSwitch(
            dl,
            text="Open folder after download",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface,
            progress_color=s.primary,
            variable=self._open_var,
            command=self._save_open_pref,
        )
        if self._open_var.get():
            open_switch.select()
        dl.add_row(open_switch)
        dl.add_spacer()

        # ── Network ──────────────────────────────────────────────────────────
        net = _SettingsSection(self, "Network")
        net.grid(row=3, column=0, padx=32, pady=8, sticky="ew")

        proxy_row = ctk.CTkFrame(net, fg_color="transparent")
        proxy_row.columnconfigure(1, weight=1)
        ctk.CTkLabel(
            proxy_row, text="HTTP Proxy",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface, width=120, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._proxy_var = tk.StringVar(value=self._settings.get("proxy", ""))
        proxy_entry = M3TextField(proxy_row, placeholder="http://host:port  (leave blank to disable)")
        proxy_entry.configure(textvariable=self._proxy_var, height=38)
        proxy_entry.grid(row=0, column=1, sticky="ew", padx=(8,0))
        net.add_row(proxy_row)
        net.add_spacer()

        # Save network button
        M3FilledButton(
            net, text="Save settings",
            command=self._save_all,
        ).grid(row=net._row, column=0, padx=20, pady=(4,16), sticky="ew")
        net._row += 1

        # ── About ─────────────────────────────────────────────────────────────
        about = _SettingsSection(self, "About")
        about.grid(row=4, column=0, padx=32, pady=(8,32), sticky="ew")

        for text in [
            f"Ploxt Desktop  v{APP_VERSION}",
            "Powered by yt-dlp - UI: CustomTkinter",
            "Inspired by JunkFood02's Android downloader",
        ]:
            ctk.CTkLabel(
                about, text=text,
                font=ctk.CTkFont(*TypeScale.body_small),
                text_color=s.on_surface_var,
            ).grid(row=about._row, column=0, padx=20, pady=2)
            about._row += 1
        about.add_spacer()

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        ThemeManager.toggle_mode(self._win)

    def _browse_dir(self) -> None:
        d = filedialog.askdirectory(
            initialdir=self._dir_var.get() or str(Path.home()),
        )
        if d:
            self._dir_var.set(d)

    def _on_fmt_change(self, choice: str) -> None:
        fmt_map = {
            "Best (auto)" : "bestvideo+bestaudio/best",
            "1080p"       : "bestvideo[height<=1080]+bestaudio/best",
            "720p"        : "bestvideo[height<=720]+bestaudio/best",
            "480p"        : "bestvideo[height<=480]+bestaudio/best",
            "Audio Only (MP3)": "bestaudio/best",
        }
        self._settings.set("default_format", fmt_map.get(choice, "bestvideo+bestaudio/best"))

    def _save_open_pref(self) -> None:
        self._settings.set("open_folder_after", self._open_var.get())

    def _save_all(self) -> None:
        self._settings.set("download_dir", self._dir_var.get())
        self._settings.set("proxy", self._proxy_var.get())
        from tkinter import messagebox
        messagebox.showinfo("Saved", "Settings saved successfully.")
