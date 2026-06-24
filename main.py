"""
Ploxt Desktop - Material You Video Downloader
Entry point. Initialises the CustomTkinter runtime, applies the Material 3
theme, and launches the root window.

Usage:
    python main.py
"""

import sys
import customtkinter as ctk
from ui.app_window import AppWindow
from core.theme import ThemeManager

def main() -> None:
    # ── CustomTkinter global appearance ─────────────────────────────────────
    ctk.set_appearance_mode("dark")          # "dark" | "light" | "system"
    ctk.set_default_color_theme("blue")      # we override everything in theme.py

    # ── Root window ─────────────────────────────────────────────────────────
    root = ctk.CTk()
    root.title("Ploxt - Video Downloader")
    root.geometry("1100x720")
    root.minsize(900, 600)

    # Apply our Material You surface colours to the root
    ThemeManager.apply_root(root)

    # ── Bootstrap the application shell ─────────────────────────────────────
    app = AppWindow(root)
    app.pack(fill="both", expand=True)

    # ── Start the event loop ─────────────────────────────────────────────────
    root.mainloop()


if __name__ == "__main__":
    main()
