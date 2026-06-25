"""
core/theme.py
─────────────────────────────────────────────────────────────────
Material-inspired colour tokens, typography scale, and shape constants.

This module provides color and shape tokens used across the UI. The
colors are adapted from Material palettes for visual consistency, but
this repository does not implement a full Material 3 system — it only
uses color tokens and shape constants inspired by that design language.
"""

from __future__ import annotations
import customtkinter as ctk


# ─────────────────────────────── Colour Tokens ─────────────────────────────

class M3Dark:
    """Dark-scheme tokens (palette adapted from Material-inspired tokens)."""
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
    """Light-scheme tokens (palette adapted from Material-inspired tokens)."""
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


# ─────────────────────────────── Shape Tokens ─────────────────────────────

class Shape:
    extra_small  = 4
    small        = 8
    medium       = 12
    large        = 16    # cards, dialogs
    extra_large  = 28    # FAB, chips
    full         = 50    # circular


# ─────────────────────────────── Typography ──────────────────────────────

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


# ─────────────────────────────── ThemeManager ────────────────────────────

class ThemeManager:
    """
    Utility class that exposes the active scheme and patches the
    root window background so it matches the chosen surface.

    This implementation attempts to proactively reconfigure existing
    widgets when the appearance mode changes. CustomTkinter updates
    some internals when `ctk.set_appearance_mode()` is called, but
    many widgets (especially custom ones) may need an explicit
    reconfigure to pick up new colors. The helper below uses a
    best-effort heuristic to apply common color-related options on
    existing widgets and their children.
    """
    _mode: str = "dark"

    # Convenience aliases — updated whenever toggle_mode() is called
    scheme: type = M3Dark

    @classmethod
    def _apply_to_widget(cls, widget) -> None:
        """
        Try to configure common color attributes on widget and recurse.
        This is heuristic: some widgets accept 'fg_color'/'bg'/'bg_color' etc.
        Unsupported options are ignored.
        """
        s = cls.scheme
        # common color attributes used by CustomTkinter and Tk widgets
        attrs = {
            "fg_color": s.surface_container,
            "bg": s.surface,
            "bg_color": s.surface,
            "fg": s.on_surface,
            "text_color": s.on_surface,
        }

        for name, value in attrs.items():
            try:
                widget.configure(**{name: value})
            except Exception:
                # widget might not support the option; ignore
                pass

        # recurse into children
        try:
            for child in widget.winfo_children():
                cls._apply_to_widget(child)
        except Exception:
            pass

    @classmethod
    def apply_root(cls, root: ctk.CTk) -> None:
        """
        Apply the active scheme to the root window and attempt to
        push colors to already-mounted widgets.
        """
        try:
            # CustomTkinter uses 'fg_color' on CTk frames/windows
            root.configure(fg_color=cls.scheme.surface)
        except Exception:
            try:
                root.configure(bg=cls.scheme.surface)
            except Exception:
                pass

        # Best-effort propagation to children to avoid stale colours
        try:
            cls._apply_to_widget(root)
        except Exception:
            pass

        # Ensure pending drawing operations run
        try:
            root.update_idletasks()
        except Exception:
            pass

    @classmethod
    def toggle_mode(cls, root: ctk.CTk) -> None:
        """
        Toggle between 'dark' and 'light' appearance, update the
        active color scheme, and re-apply colors to the UI.
        """
        # flip mode
        if cls._mode == "dark":
            cls._mode = "light"
            cls.scheme = M3Light
            ctk.set_appearance_mode("light")
        else:
            cls._mode = "dark"
            cls.scheme = M3Dark
            ctk.set_appearance_mode("dark")

        # Re-apply colours to root and try to refresh widgets.
        cls.apply_root(root)

    @classmethod
    def is_dark(cls) -> bool:
        return cls._mode == "dark"

    # ── Helper: returns (fg_color, text_color) for surface cards ────────
    @classmethod
    def card_colors(cls):
        s = cls.scheme
        return s.surface_container, s.on_surface

    @classmethod
    def primary_colors(cls):
        s = cls.scheme
        return s.primary, s.on_primary
