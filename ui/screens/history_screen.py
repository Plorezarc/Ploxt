"""
ui/screens/history_screen.py
─────────────────────────────────────────────────────────────────────────────
Download History screen.

Lists every past download as a compact card row with title, date,
format, and an "Open folder" shortcut.
"""

from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from tkinter import messagebox
import customtkinter as ctk

from core.theme import ThemeManager, TypeScale
from core.history import HistoryManager
from ui.components.m3_widgets import (
    M3Card, M3SectionLabel, M3OutlinedButton, M3TonalButton,
    M3StatusBadge, M3Divider,
)


def _open_folder(path: str) -> None:
    """Cross-platform reveal folder in file manager."""
    p = Path(path)
    if not p.exists():
        messagebox.showwarning("Folder not found", f"Could not find:\n{path}")
        return
    if sys.platform == "win32":
        os.startfile(str(p))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(p)])
    else:
        subprocess.Popen(["xdg-open", str(p)])


def _fmt_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.astimezone().strftime("%d %b %Y  %H:%M")
    except Exception:
        return iso


class _HistoryRow(M3Card):
    """One row in the history list."""

    def __init__(self, master, record: dict, on_delete: callable, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(1, weight=1)
        s = ThemeManager.scheme

        # Status dot
        M3StatusBadge(self, status=record.get("status", "done")).grid(
            row=0, column=0, rowspan=2, padx=(16,8), pady=14,
        )

        # Title
        ctk.CTkLabel(
            self, text=record.get("title", "Unknown")[:80],
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface, anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(14,2))

        # Meta
        meta = f"{_fmt_date(record.get('timestamp',''))}  -  {record.get('format','')}"
        ctk.CTkLabel(
            self, text=meta,
            font=ctk.CTkFont(*TypeScale.body_small),
            text_color=s.on_surface_var, anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(0,14))

        # Buttons
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=0, column=2, rowspan=2, padx=(8,16), pady=14)

        M3TonalButton(
            btns, text="Open", width=88, height=34,
            command=lambda: _open_folder(record.get("out_path", "")),
        ).pack(pady=(0,4))

        M3OutlinedButton(
            btns, text="Delete", width=88, height=34,
            command=lambda: on_delete(record["id"]),
        ).pack()


class HistoryScreen(ctk.CTkScrollableFrame):
    """Download history list screen."""

    def __init__(self, master, history_mgr: HistoryManager, **kwargs):
        s = ThemeManager.scheme
        kwargs.setdefault("fg_color", s.surface)
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("scrollbar_button_color", s.outline_variant)
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)

        self._hist = history_mgr
        self._rows: dict[str, _HistoryRow] = {}

        self._build()

    def _build(self) -> None:
        s = ThemeManager.scheme

        # ── Header ───────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(32,20))
        hdr.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="History",
            font=ctk.CTkFont("", 28, "bold"),
            text_color=s.on_surface, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        M3OutlinedButton(hdr, text="Clear all", width=96,
                         command=self._clear_all).grid(row=0, column=1)

        # ── List ─────────────────────────────────────────────────────────────
        self._list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._list_frame.grid(row=1, column=0, sticky="ew", padx=32)
        self._list_frame.columnconfigure(0, weight=1)

        self._empty_lbl = ctk.CTkLabel(
            self, text="No downloads yet.\nYour download history will appear here.",
            font=ctk.CTkFont(*TypeScale.body_medium),
            text_color=s.on_surface_var, justify="center",
        )

        self.refresh()

    def refresh(self) -> None:
        """Re-render the list from the history manager."""
        # Destroy old rows
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._rows.clear()

        records = self._hist.all()
        if not records:
            self._empty_lbl.grid(row=2, column=0, pady=60)
            return

        self._empty_lbl.grid_forget()

        for i, rec in enumerate(records):
            row = _HistoryRow(
                self._list_frame, rec,
                on_delete=self._delete_record,
            )
            row.grid(row=i, column=0, sticky="ew", pady=5)
            self._rows[rec["id"]] = row

    def add_record(self, record: dict) -> None:
        """Add a single new record at the top without full refresh."""
        self.refresh()   # simple approach — refresh entire list

    def _delete_record(self, record_id: str) -> None:
        self._hist.remove(record_id)
        self.refresh()

    def _clear_all(self) -> None:
        if messagebox.askyesno("Clear History", "Delete all download history?"):
            self._hist.clear()
            self.refresh()
