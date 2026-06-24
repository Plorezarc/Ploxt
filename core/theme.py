"""
core/theme.py
─────────────────────────────────────────────────────────────────────────────
Material You colour tokens, typography scale, and shape constants.

Ported from the original Material You palette:
  Original Material You color tokens.

Design decisions
  • Dark  surface  : #121318  (MD3 Surface)
  • Light surface  : #F9F9FF  (MD3 Surface)
  • Primary accent : #BEC2FF  (muted cornflower default seed)
  • Corner radius  : 16 dp equivalent (used on cards, dialogs)
  • Font            : system default (falls back to Inter/Segoe gracefully)
"""

from __future__ import annotations
import customtkinter as ctk


# ─────────────────────────────── Colour Tokens ───────────────────────────────

class M3Dark:
    """Material 3 dark-scheme tokens."""
    # Surfaces
    surface          = "#141218"
    surface_dim      = "#141218"
    surface_variant  = "#49454F"
    surface_container= "#211F26"
    outline_variant  = "#49454F"
    outline          = "#938F99"

    # Primary
    primary          = "#D0BCFF"
    on_primary       = "#381E72"
    primary_container= "#4F378B"
    on_primary_cont  = "#EADDFF"

    # Secondary
    secondary        = "#CCC2DC"
    secondary_cont   = "#4A4458"
    on_secondary_cont= "#E8DEF8"

    # Tertiary
    tertiary         = "#EFB8C8"
    tertiary_cont    = "#633B48"

    # Error
    error            = "#F2B8B5"
    error_cont       = "#8C1D18"
    on_error_cont    = "#F9DEDC"

    # On-colours
    on_surface       = "#E6E0E9"
    on_surface_var   = "#CAC4D0"
    on_background    = "#E6E0E9"
    background       = "#141218"


class M3Light:
    """Material 3 light-scheme tokens."""
    surface          = "#FFFBFE"
    surface_dim      = "#DED8E1"
    surface_variant  = "#E7E0EC"
    surface_container= "#F3EDF7"
    outline_variant  = "#CAC4D0"
    outline          = "#79747E"

    primary          = "#6750A4"
    on_primary       = "#FFFFFF"
    primary_container= "#EADDFF"
    on_primary_cont  = "#21005D"

    secondary        = "#625B71"
    secondary_cont   = "#E8DEF8"
    on_secondary_cont= "#1D192B"

    tertiary         = "#7D5260"
    tertiary_cont    = "#FFD8E4"

    error            = "#B3261E"
    error_cont       = "#F9DEDC"
    on_error_cont    = "#410E0B"

    on_surface       = "#1C1B1F"
    on_surface_var   = "#49454F"
    on_background    = "#1C1B1F"
    background       = "#FFFBFE"


# ─────────────────────────────── Shape Tokens ────────────────────────────────

class Shape:
    extra_small  = 4
    small        = 8
    medium       = 12
    large        = 16    # cards, dialogs
    extra_large  = 28    # FAB, chips
    full         = 50    # circular


# ─────────────────────────────── Typography ──────────────────────────────────

class TypeScale:
    display_large  = ("", 57, "normal")
    display_medium = ("", 45, "normal")
    display_small  = ("", 36, "normal")
    headline_large = ("", 32, "normal")
    headline_medium= ("", 28, "normal")
    headline_small = ("", 24, "normal")
    title_large    = ("", 22, "normal")
    title_medium   = ("", 16, "bold")
    title_small    = ("", 14, "bold")
    label_large    = ("", 14, "bold")
    label_medium   = ("", 12, "bold")
    label_small    = ("", 11, "bold")
    body_large     = ("", 16, "normal")
    body_medium    = ("", 14, "normal")
    body_small     = ("", 12, "normal")


# ─────────────────────────────── ThemeManager ────────────────────────────────

class ThemeManager:
    """
    Utility class that exposes the active scheme and patches the
    root window background so it matches Material 3 surface.
    """
    _mode: str = "dark"

    # Convenience aliases — updated whenever toggle_mode() is called
    scheme: type = M3Dark

    @classmethod
    def apply_root(cls, root: ctk.CTk) -> None:
        root.configure(fg_color=cls.scheme.surface)

    @classmethod
    def toggle_mode(cls, root: ctk.CTk) -> None:
        if cls._mode == "dark":
            cls._mode = "light"
            cls.scheme = M3Light
            ctk.set_appearance_mode("light")
        else:
            cls._mode = "dark"
            cls.scheme = M3Dark
            ctk.set_appearance_mode("dark")
        cls.apply_root(root)

    @classmethod
    def is_dark(cls) -> bool:
        return cls._mode == "dark"

    # ── Helper: returns (fg_color, text_color) for surface cards ────────────
    @classmethod
    def card_colors(cls):
        s = cls.scheme
        return s.surface_container, s.on_surface

    @classmethod
    def primary_colors(cls):
        s = cls.scheme
        return s.primary, s.on_primary
